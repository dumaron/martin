from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from openpyxl import Workbook

from core.models import BankFileImport


class BankFileImportFinecoHeaderDetectionTest(TestCase):
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
		"""Test _find_fineco_header_row when Data_Operazione is in the first row (no introduction)."""
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
		"""Test _find_fineco_header_row when Data_Operazione is in the second row (1 introduction row)."""
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
		"""Test _find_fineco_header_row when Data_Operazione is in the tenth row (9 introduction rows)."""
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
		"""Test that get_file_rows correctly uses the dynamic header detection."""
		# Create XLSX file with 9 introduction rows (like the old hardcoded value)
		xlsx_content = self._create_test_xlsx_file(header_rows_before_data=9)

		mock_file = SimpleUploadedFile(
			'test_fineco_integration.xlsx',
			xlsx_content.read(),
			content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		)

		# Patch save to prevent BankTransaction creation, but allow the model to be created
		with patch.object(BankFileImport, 'save', return_value=None) as mock_save:
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
