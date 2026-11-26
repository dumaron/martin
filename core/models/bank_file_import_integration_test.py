from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook

from core.models import BankAccount, BankFileImport, BankTransaction
from core.models.bank_transaction import CREDEM_BANK_ACCOUNT_ID, FINECO_BANK_ACCOUNT_ID
from core.tests.base import FileCleanupTestCase

FIXTURES = Path(__file__).parent / 'bank_file_import_fixtures'


class BankFileImportFinecoHeaderDetectionTest(FileCleanupTestCase):
	"""Test the _find_fineco_header_row method of BankFileImport model."""

	def _create_test_xlsx_file(self, header_rows_before_data):
		"""
		Create a test XLSX file with a specified number of introduction rows before the header.

		Args:
			header_rows_before_data: Number of rows to add before the Data_Operazione header row

		Returns:
			BytesIO object containing the XLSX file
		"""
		workbook = Workbook()
		sheet = workbook.active

		# Add introduction rows (e.g., bank info, account info, etc.)
		for i in range(header_rows_before_data):
			sheet.append([f'Introduction row {i + 1}', 'Some data', 'More info'])

		# Add the header row with Data_Operazione
		sheet.append(['Data_Operazione', 'Descrizione_Completa', 'Entrate', 'Uscite'])

		# Add some sample data rows
		sheet.append(['2024-12-01', 'Test Transaction 1', 100.0, 0])
		sheet.append(['2024-12-02', 'Test Transaction 2', 0, -50.0])
		sheet.append(['2024-12-03', 'Test Transaction 3', 75.5, 0])

		# Save to BytesIO
		xlsx_buffer = BytesIO()
		workbook.save(xlsx_buffer)
		xlsx_buffer.seek(0)

		return xlsx_buffer

	def test_find_fineco_header_row_with_no_introduction_rows(self):
		"""With the header in the first row, _find_fineco_header_row reports 0 rows to skip."""
		# Create XLSX file with 0 introduction rows
		xlsx_content = self._create_test_xlsx_file(header_rows_before_data=0)

		mock_file = SimpleUploadedFile(
			'test_fineco_no_intro.xlsx',
			xlsx_content.read(),
			content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		)

		# Mock the file processing to avoid actual file operations during save
		with patch.object(BankFileImport, 'get_file_rows', return_value=[]):
			file_import = BankFileImport.objects.create(
				file_type=BankFileImport.FileType.FINECO_BANK_ACCOUNT_XLSX_EXPORT, bank_file=mock_file
			)

		# Test the _find_fineco_header_row method
		rows_to_skip = file_import._find_fineco_header_row()

		# Should return 0 since Data_Operazione is in the first physical row
		# Note: tablib loads without skip_lines and uses first row as header by default,
		# so Data_Operazione appears at iteration index 0, meaning 0 rows to skip
		self.assertEqual(rows_to_skip, 0)

	def test_find_fineco_header_row_with_one_introduction_row(self):
		"""With one introduction row before the header, _find_fineco_header_row reports 1 row to skip."""
		# Create XLSX file with 1 introduction row
		xlsx_content = self._create_test_xlsx_file(header_rows_before_data=1)

		mock_file = SimpleUploadedFile(
			'test_fineco_one_intro.xlsx',
			xlsx_content.read(),
			content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		)

		# Mock the file processing to avoid actual file operations during save
		with patch.object(BankFileImport, 'get_file_rows', return_value=[]):
			file_import = BankFileImport.objects.create(
				file_type=BankFileImport.FileType.FINECO_BANK_ACCOUNT_XLSX_EXPORT, bank_file=mock_file
			)

		# Test the _find_fineco_header_row method
		rows_to_skip = file_import._find_fineco_header_row()

		# Should return 1: tablib uses intro row as header, finds Data_Operazione at index 0,
		# returns index + 1 = 1 row to skip
		self.assertEqual(rows_to_skip, 1)

	def test_find_fineco_header_row_with_nine_introduction_rows(self):
		"""With nine introduction rows before the header, _find_fineco_header_row reports 9 rows to skip."""
		# Create XLSX file with 9 introduction rows
		xlsx_content = self._create_test_xlsx_file(header_rows_before_data=9)

		mock_file = SimpleUploadedFile(
			'test_fineco_nine_intro.xlsx',
			xlsx_content.read(),
			content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		)

		# Mock the file processing to avoid actual file operations during save
		with patch.object(BankFileImport, 'get_file_rows', return_value=[]):
			file_import = BankFileImport.objects.create(
				file_type=BankFileImport.FileType.FINECO_BANK_ACCOUNT_XLSX_EXPORT, bank_file=mock_file
			)

		# Test the _find_fineco_header_row method
		rows_to_skip = file_import._find_fineco_header_row()

		# Should return 9: tablib uses first intro row as header, finds Data_Operazione at index 8,
		# returns index + 1 = 9 rows to skip
		self.assertEqual(rows_to_skip, 9)

	def test_find_fineco_header_row_integration_with_get_file_rows(self):
		"""get_file_rows skips the introduction rows and returns the 3 data rows, keyed by the header columns."""
		# Create XLSX file with 9 introduction rows (like the old hardcoded value)
		xlsx_content = self._create_test_xlsx_file(header_rows_before_data=9)

		mock_file = SimpleUploadedFile(
			'test_fineco_integration.xlsx',
			xlsx_content.read(),
			content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		)

		# Patch save to prevent BankTransaction creation, but allow the model to be created
		with patch.object(BankFileImport, 'save', return_value=None):
			file_import = BankFileImport(
				file_type=BankFileImport.FileType.FINECO_BANK_ACCOUNT_XLSX_EXPORT, bank_file=mock_file
			)
			# Manually assign the file since we're not really saving
			file_import.bank_file = mock_file

		# Call get_file_rows to test the full integration
		rows = file_import.get_file_rows()

		# Should have 3 data rows (not including header or introduction rows)
		self.assertEqual(len(rows), 3)

		# Verify the first row has the expected structure with Data_Operazione as column header
		self.assertIn('Data_Operazione', rows[0])
		self.assertIn('Descrizione_Completa', rows[0])
		self.assertIn('Entrate', rows[0])
		self.assertIn('Uscite', rows[0])


class BankFileImportSaveTest(FileCleanupTestCase):
	def setUp(self):
		BankAccount.objects.create(
			id=FINECO_BANK_ACCOUNT_ID, name='Fineco', iban='IT00X0000000000000000000002', personal=True
		)
		BankAccount.objects.create(
			id=CREDEM_BANK_ACCOUNT_ID, name='Credem', iban='IT00X0000000000000000000003', personal=False
		)

	def import_fixture(self, file_name, file_type):
		with open(FIXTURES / file_name, 'rb') as fixture:
			return BankFileImport.objects.create(file_type=file_type, bank_file=File(fixture, name=file_name))

	def test_fineco_export(self):
		"""A Fineco export stores its Data_Operazione as booking date and the date in the description as transaction date, skipping the rows not yet booked."""
		self.import_fixture('fineco_export.xlsx', BankFileImport.FileType.FINECO_BANK_ACCOUNT_XLSX_EXPORT)

		self.assertEqual(
			list(
				BankTransaction.objects.order_by('booking_date', 'amount').values_list(
					'transaction_date', 'booking_date', 'date', 'amount'
				)
			),
			[
				(date(2026, 10, 12), date(2026, 10, 14), date(2026, 10, 12), Decimal('-50.00')),
				(date(2026, 10, 23), date(2026, 10, 23), date(2026, 10, 23), Decimal('-150.00')),
				(date(2026, 10, 27), date(2026, 10, 27), date(2026, 10, 27), Decimal('2500.50')),
				(date(2026, 10, 26), date(2026, 10, 28), date(2026, 10, 26), Decimal('-2.00')),
				(None, date(2026, 11, 5), date(2026, 11, 5), Decimal('-3.95')),
			],
		)

	def test_credem_export(self):
		"""A Credem export stores its Data contabile as booking date, the date in the description as transaction date, and collapses the spaces of the description."""
		self.import_fixture('credem_export.csv', BankFileImport.FileType.CREDEM_CSV_EXPORT)

		self.assertEqual(
			list(
				BankTransaction.objects.order_by('booking_date', 'amount').values_list(
					'transaction_date', 'booking_date', 'date', 'amount'
				)
			),
			[
				(None, date(2026, 8, 6), date(2026, 8, 6), Decimal('-1608.90')),
				(None, date(2026, 10, 27), date(2026, 10, 27), Decimal('-744.50')),
				(date(2026, 10, 28), date(2026, 10, 30), date(2026, 10, 28), Decimal('-122.02')),
				(None, date(2026, 10, 30), date(2026, 10, 30), Decimal('2000.00')),
			],
		)
		self.assertEqual(
			BankTransaction.objects.get(amount=Decimal('-122.02')).description,
			'PAGAMENTO DEBINT PAGAMENTO CARTA DI DEBITO INTERNAZIONALE 537572******0000 -28/10/26-19:33 ROSSI '
			'AMAZON* B27GE7IZ4 LUXEMBOU',
		)

	def test_fineco_export_imported_twice(self):
		"""Importing the same Fineco export twice adds no transaction the second time."""
		self.import_fixture('fineco_export.xlsx', BankFileImport.FileType.FINECO_BANK_ACCOUNT_XLSX_EXPORT)
		self.import_fixture('fineco_export.xlsx', BankFileImport.FileType.FINECO_BANK_ACCOUNT_XLSX_EXPORT)

		self.assertEqual(BankTransaction.objects.count(), 5)

	def test_credem_export_imported_twice(self):
		"""Importing the same Credem export twice adds no transaction the second time."""
		self.import_fixture('credem_export.csv', BankFileImport.FileType.CREDEM_CSV_EXPORT)
		self.import_fixture('credem_export.csv', BankFileImport.FileType.CREDEM_CSV_EXPORT)

		self.assertEqual(BankTransaction.objects.count(), 4)
