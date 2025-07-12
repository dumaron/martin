from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from core.models import BankAccount, BankFileImport, BankTransaction



class BankTransactionGetPotentialDuplicateTest(TestCase):
	"""Test the get_potential_duplicate method of BankTransaction model."""

	def setUp(self):
		"""Set up test data."""
		# Create a test bank account
		self.bank_account = BankAccount.objects.create(
			name='Test Bank Account',
			iban='IT60X0542811101000000123456',
			personal=True
		)

		# Create a mock CSV file for testing
		test_csv_content = 'Data;Descrizione;Importo\n2024-01-15;Test transaction;100.50'
		mock_file = SimpleUploadedFile('test_import.csv', test_csv_content.encode('utf-8'), content_type='text/csv')

		# Mock the file processing to avoid actual file operations during testing
		with patch.object(BankFileImport, 'get_file_rows', return_value=[]):
			self.file_import = BankFileImport.objects.create(
				file_name='test_import.csv',
				file_type=BankFileImport.FileType.UNICREDIT_BANK_ACCOUNT_CSV_EXPORT,
				bank_file=mock_file
			)

	def test_get_potential_duplicate_returns_none_when_no_duplicates(self):
		"""Test that get_potential_duplicate returns None when no duplicates exist."""
		transaction = BankTransaction.objects.create(
			name='Test Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		result = transaction.get_potential_duplicate()

		self.assertIsNone(result)

	def test_get_potential_duplicate_returns_transaction_when_exact_match_exists(self):
		"""Test that get_potential_duplicate returns a transaction when exact match exists (same amount, date, different name)."""
		# Create first transaction
		transaction1 = BankTransaction.objects.create(
			name='Original Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		# Create second transaction with same amount and date but different name
		transaction2 = BankTransaction.objects.create(
			name='Different Transaction Name',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		result = transaction2.get_potential_duplicate()

		# Should return the first transaction as potential duplicate
		self.assertEqual(result, transaction1)

	def test_get_potential_duplicate_returns_none_when_only_amount_matches(self):
		"""Test that get_potential_duplicate returns None when only amount matches but date differs."""
		# Create first transaction
		BankTransaction.objects.create(
			name='Original Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		# Create second transaction with same amount but different date
		transaction2 = BankTransaction.objects.create(
			name='Different Transaction',
			date=date(2024, 1, 16),  # Different date
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		result = transaction2.get_potential_duplicate()

		# Should return None since date differs
		self.assertIsNone(result)

	def test_get_potential_duplicate_returns_none_when_only_date_matches(self):
		"""Test that get_potential_duplicate returns None when only date matches but amount differs."""
		# Create first transaction
		BankTransaction.objects.create(
			name='Original Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		# Create second transaction with same date but different amount
		transaction2 = BankTransaction.objects.create(
			name='Different Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('200.75'),  # Different amount
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		result = transaction2.get_potential_duplicate()

		# Should return None since amount differs
		self.assertIsNone(result)

	def test_get_potential_duplicate_returns_first_match_when_multiple_duplicates_exist(self):
		"""Test that get_potential_duplicate returns first match when multiple duplicates exist."""
		# Create first transaction
		transaction1 = BankTransaction.objects.create(
			name='First Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		# Create second transaction with same amount and date
		BankTransaction.objects.create(
			name='Second Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		# Create third transaction with same amount and date
		transaction3 = BankTransaction.objects.create(
			name='Third Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		result = transaction3.get_potential_duplicate()

		# Should return the first transaction (first match)
		self.assertEqual(result, transaction1)

	def test_get_potential_duplicate_works_across_different_bank_accounts(self):
		"""Test that get_potential_duplicate works across different bank accounts."""
		# Create second bank account
		bank_account2 = BankAccount.objects.create(
			name='Second Bank Account',
			iban='IT60X0542811101000000654321',
			personal=True
		)

		# Create transaction in first bank account
		transaction1 = BankTransaction.objects.create(
			name='Transaction Bank 1',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		# Create transaction in second bank account with same amount and date
		transaction2 = BankTransaction.objects.create(
			name='Transaction Bank 2',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=bank_account2
		)

		result = transaction2.get_potential_duplicate()

		# Should find the transaction from the other bank account
		self.assertEqual(result, transaction1)


class BankTransactionFromFinecoXslxRowTest(TestCase):
	"""Test the from_fineco_bank_account_xslx_row static method of BankTransaction model."""

	def setUp(self):
		# Create a mock XLSX file for testing
		test_xlsx_content = b'Test XLSX content'
		mock_file = SimpleUploadedFile('test_fineco.xlsx', test_xlsx_content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

		# Mock the file processing to avoid actual file operations during testing
		with patch.object(BankFileImport, 'get_file_rows', return_value=[]):
			self.file_import = BankFileImport.objects.create(
				file_name='test_fineco.xlsx',
				file_type=BankFileImport.FileType.FINECO_BANK_ACCOUNT_XLSX_EXPORT,
				bank_file=mock_file
			)

	def test_from_fineco_bank_account_xslx_row_with_income_only(self):
		"""Test creating BankTransaction from Fineco XLSX row with income only."""
		row = {
			'Descrizione_Completa': '  Test Income Transaction  ',
			'Entrate': 150.75,
			'Uscite': 0,
			'Data_Operazione': date(2024, 3, 15)
		}

		transaction = BankTransaction.from_fineco_bank_account_xslx_row(row, self.file_import)

		self.assertEqual(transaction.name, 'Test Income Transaction')
		self.assertEqual(transaction.amount, 150.75)
		self.assertEqual(transaction.date, date(2024, 3, 15))
		self.assertEqual(transaction.file_import, self.file_import)
		self.assertEqual(transaction.bank_account_id, 2)  # FINECO_BANK_ACCOUNT_ID

	def test_from_fineco_bank_account_xslx_row_with_expense_only(self):
		"""Test creating BankTransaction from Fineco XLSX row with expense only."""
		row = {
			'Descrizione_Completa': 'Test Expense Transaction',
			'Entrate': 0,
			'Uscite': -85.30,
			'Data_Operazione': date(2024, 3, 20)
		}

		transaction = BankTransaction.from_fineco_bank_account_xslx_row(row, self.file_import)

		self.assertEqual(transaction.name, 'Test Expense Transaction')
		self.assertEqual(transaction.amount, -85.30)
		self.assertEqual(transaction.date, date(2024, 3, 20))
		self.assertEqual(transaction.file_import, self.file_import)
		self.assertEqual(transaction.bank_account_id, 2)  # FINECO_BANK_ACCOUNT_ID

	def test_from_fineco_bank_account_xslx_row_with_both_values(self):
		"""Test creating BankTransaction from Fineco XLSX row with both income and expense values."""
		row = {
			'Descrizione_Completa': 'Transaction with both values',
			'Entrate': 100.0,
			'Uscite': -25.0,
			'Data_Operazione': date(2024, 3, 25)
		}

		transaction = BankTransaction.from_fineco_bank_account_xslx_row(row, self.file_import)

		self.assertEqual(transaction.name, 'Transaction with both values')
		self.assertEqual(transaction.amount, 75.0)  # 100.0 + (-25.0)
		self.assertEqual(transaction.date, date(2024, 3, 25))
		self.assertEqual(transaction.file_import, self.file_import)
		self.assertEqual(transaction.bank_account_id, 2)

	def test_from_fineco_bank_account_xslx_row_with_zero_values(self):
		"""Test creating BankTransaction from Fineco XLSX row with zero values."""
		row = {
			'Descrizione_Completa': 'Zero amount transaction',
			'Entrate': 0,
			'Uscite': 0,
			'Data_Operazione': date(2024, 3, 30)
		}

		transaction = BankTransaction.from_fineco_bank_account_xslx_row(row, self.file_import)

		self.assertEqual(transaction.name, 'Zero amount transaction')
		self.assertEqual(transaction.amount, 0.0)
		self.assertEqual(transaction.date, date(2024, 3, 30))
		self.assertEqual(transaction.file_import, self.file_import)
		self.assertEqual(transaction.bank_account_id, 2)

	def test_from_fineco_bank_account_xslx_row_with_none_values(self):
		"""Test creating BankTransaction from Fineco XLSX row with None values (empty cells)."""
		row = {
			'Descrizione_Completa': 'Transaction with None values',
			'Entrate': None,
			'Uscite': None,
			'Data_Operazione': date(2024, 4, 1)
		}

		transaction = BankTransaction.from_fineco_bank_account_xslx_row(row, self.file_import)

		self.assertEqual(transaction.name, 'Transaction with None values')
		self.assertEqual(transaction.amount, 0.0)  # None or 0 + None or 0 = 0.0
		self.assertEqual(transaction.date, date(2024, 4, 1))
		self.assertEqual(transaction.file_import, self.file_import)
		self.assertEqual(transaction.bank_account_id, 2)

	def test_from_fineco_bank_account_xslx_row_with_mixed_none_and_value(self):
		"""Test creating BankTransaction from Fineco XLSX row with mixed None and numeric values."""
		row = {
			'Descrizione_Completa': 'Mixed None and value',
			'Entrate': 250.0,
			'Uscite': None,
			'Data_Operazione': date(2024, 4, 5)
		}

		transaction = BankTransaction.from_fineco_bank_account_xslx_row(row, self.file_import)

		self.assertEqual(transaction.name, 'Mixed None and value')
		self.assertEqual(transaction.amount, 250.0)  # 250.0 + 0
		self.assertEqual(transaction.date, date(2024, 4, 5))
		self.assertEqual(transaction.file_import, self.file_import)
		self.assertEqual(transaction.bank_account_id, 2)

	def test_from_fineco_bank_account_xslx_row_strips_whitespace_from_description(self):
		"""Test that description whitespace is properly stripped."""
		row = {
			'Descrizione_Completa': '   \t  Whitespace Transaction  \n  ',
			'Entrate': 100.0,
			'Uscite': 0,
			'Data_Operazione': date(2024, 4, 10)
		}

		transaction = BankTransaction.from_fineco_bank_account_xslx_row(row, self.file_import)

		self.assertEqual(transaction.name, 'Whitespace Transaction')

	def test_from_fineco_bank_account_xslx_row_with_decimal_amounts(self):
		"""Test creating BankTransaction from Fineco XLSX row with decimal amounts."""
		row = {
			'Descrizione_Completa': 'Decimal Transaction',
			'Entrate': 123.456,
			'Uscite': -45.789,
			'Data_Operazione': date(2024, 4, 15)
		}

		transaction = BankTransaction.from_fineco_bank_account_xslx_row(row, self.file_import)

		self.assertEqual(transaction.name, 'Decimal Transaction')
		self.assertAlmostEqual(transaction.amount, 77.667, places=3)  # 123.456 + (-45.789)
		self.assertEqual(transaction.date, date(2024, 4, 15))
		self.assertEqual(transaction.file_import, self.file_import)
		self.assertEqual(transaction.bank_account_id, 2)


