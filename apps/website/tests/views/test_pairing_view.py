from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from core.models import BankAccount, BankFileImport, BankTransaction


class PairingViewTest(TestCase):
	"""Test the pairing view."""

	def setUp(self):
		"""Set up test data."""
		# Create a test user
		self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')

		# Create a test bank account
		self.bank_account = BankAccount.objects.create(
			name='Test Bank Account', iban='IT60X0542811101000000123456', personal=True
		)

		# Create a mock CSV file for testing
		test_csv_content = 'Data;Descrizione;Importo\n2024-01-15;Test transaction;100.50'
		mock_file = SimpleUploadedFile('test_import.csv', test_csv_content.encode('utf-8'), content_type='text/csv')

		# Mock the file processing to avoid actual file operations during testing
		with patch.object(BankFileImport, 'get_file_rows', return_value=[]):
			self.file_import = BankFileImport.objects.create(
				file_name='test_import.csv',
				file_type=BankFileImport.FileType.UNICREDIT_BANK_ACCOUNT_CSV_EXPORT,
				bank_file=mock_file,
			)

		# Create test transactions
		self.original_transaction = BankTransaction.objects.create(
			name='Original Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		self.duplicate_transaction = BankTransaction.objects.create(
			name='Duplicate Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
			duplicate_of=self.original_transaction,
		)

		self.client = Client()

	@patch.object(BankTransaction, 'get_similar_transactions')
	def test_pairing_view_excludes_duplicates(self, mock_get_similar):
		"""Test that the pairing view excludes transactions marked as duplicates."""
		mock_get_similar.return_value = BankTransaction.objects.none()

		self.client.force_login(self.user)

		# Get the pairing view for personal transactions
		url = reverse('pairing', kwargs={'kind': 'personal'})
		response = self.client.get(url)

		# Should return 200 OK
		self.assertEqual(response.status_code, 200)

		# The view should show the original transaction, not the duplicate
		self.assertEqual(response.context['expense'], self.original_transaction)
		self.assertNotEqual(response.context['expense'], self.duplicate_transaction)

	@patch.object(BankTransaction, 'get_similar_transactions')
	def test_pairing_view_with_only_duplicates(self, mock_get_similar):
		"""Test that the pairing view shows empty when only duplicates exist."""
		mock_get_similar.return_value = BankTransaction.objects.none()

		self.client.force_login(self.user)

		# Mark the original transaction as a duplicate too
		self.original_transaction.duplicate_of = self.duplicate_transaction
		self.original_transaction.save()

		# Get the pairing view for personal transactions
		url = reverse('pairing', kwargs={'kind': 'personal'})
		response = self.client.get(url)

		# Should return 200 OK but show empty template
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'pairing_empty.html')

	@patch.object(BankTransaction, 'get_similar_transactions')
	def test_pairing_view_shows_difflib_for_potential_duplicates(self, mock_get_similar):
		"""Test that the pairing view shows difflib output for potential duplicates."""
		mock_get_similar.return_value = BankTransaction.objects.none()

		# Remove existing transactions to have a clean slate
		BankTransaction.objects.all().delete()

		# Create a main transaction (will be shown in pairing view)
		BankTransaction.objects.create(
			name='Main Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# Create a potential duplicate with slightly different name but same date/amount
		BankTransaction.objects.create(
			name='Slightly Different Transaction Name',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		self.client.force_login(self.user)

		# Get the pairing view for personal transactions
		url = reverse('pairing', kwargs={'kind': 'personal'})
		response = self.client.get(url)

		# Should return 200 OK
		self.assertEqual(response.status_code, 200)

		# Should have potential_duplicate in context
		self.assertIsNotNone(response.context['potential_duplicate'])

		# Should have potential_duplicate_highlighted in context
		self.assertIsNotNone(response.context['potential_duplicate_highlighted'])

		# The highlighted content should contain HTML spans for differences
		highlighted_content = response.context['potential_duplicate_highlighted']
		self.assertIn('<span style=', highlighted_content)
		self.assertIn('background-color: #ffcccc', highlighted_content)
