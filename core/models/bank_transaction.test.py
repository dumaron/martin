from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

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


class PairingViewIntegrationTest(TestCase):
	"""Integration test for pairing view with potential duplicate widget."""

	def setUp(self):
		"""Set up test data."""
		# Create a test user and client
		self.user = User.objects.create_user(username='testuser', password='testpass')
		self.client = Client()
		self.client.login(username='testuser', password='testpass')

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

	@patch('apps.website.views.get_similar_bank_transactions')
	def test_pairing_view_displays_potential_duplicate_widget_when_duplicate_exists(self, mock_get_similar):
		"""Test that pairing view displays potential duplicate widget when a duplicate exists."""
		# Mock the similar bank transactions function to avoid FTS table dependency
		mock_get_similar.return_value = []
		
		# Create first transaction (this will be the one shown in pairing view since it's oldest)
		current_transaction = BankTransaction.objects.create(
			name='Current Transaction',
			date=date(2024, 1, 14),  # Earlier date so it's shown first
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		# Create second transaction (potential duplicate with same date and amount)
		duplicate_transaction = BankTransaction.objects.create(
			name='Original Transaction',
			date=date(2024, 1, 14),  # Same date for duplicate detection
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		# Get the pairing view
		response = self.client.get(reverse('pairing', kwargs={'kind': 'personal'}))

		# Check that the response is successful
		self.assertEqual(response.status_code, 200)

		# Check that the potential duplicate warning is present in the HTML
		self.assertContains(response, 'Potential duplicate detected')
		self.assertContains(response, 'Original Transaction')

		# Check that the potential duplicate data is passed to the template
		self.assertIsNotNone(response.context['potential_duplicate'])
		# The current transaction should find the duplicate transaction
		self.assertEqual(response.context['potential_duplicate'], duplicate_transaction)

	@patch('apps.website.views.get_similar_bank_transactions')
	def test_pairing_view_does_not_display_potential_duplicate_widget_when_no_duplicate(self, mock_get_similar):
		"""Test that pairing view does not display potential duplicate widget when no duplicate exists."""
		# Mock the similar bank transactions function to avoid FTS table dependency
		mock_get_similar.return_value = []
		
		# Create only one transaction (no duplicate)
		BankTransaction.objects.create(
			name='Single Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		# Get the pairing view
		response = self.client.get(reverse('pairing', kwargs={'kind': 'personal'}))

		# Check that the response is successful
		self.assertEqual(response.status_code, 200)

		# Check that the potential duplicate warning is NOT present in the HTML
		self.assertNotContains(response, 'Potential duplicate detected')

		# Check that potential_duplicate is None in the context
		self.assertIsNone(response.context['potential_duplicate'])

