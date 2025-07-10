from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from core.models import BankAccount, BankFileImport, BankTransaction


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

		# Create a second transaction (potential duplicate with same date and amount)
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
