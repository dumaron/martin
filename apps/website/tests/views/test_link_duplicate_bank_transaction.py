from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from core.models import BankAccount, BankFileImport, BankTransaction


class LinkDuplicateBankTransactionViewTest(TestCase):
	"""Test the link_duplicate_bank_transaction view."""

	def setUp(self):
		"""Set up test data."""
		# Create a test user
		self.user = User.objects.create_user(
			username='testuser',
			email='test@example.com',
			password='testpass123'
		)
		
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

		# Create test transactions
		self.original_transaction = BankTransaction.objects.create(
			name='Original Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		self.duplicate_transaction = BankTransaction.objects.create(
			name='Duplicate Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)

		self.client = Client()

	def test_requires_login(self):
		"""Test that the view requires authentication."""
		url = reverse('link-duplicate-bank-transaction', kwargs={'duplicate_transaction_id': self.duplicate_transaction.id})
		response = self.client.get(url)
		
		# Should redirect to login
		self.assertEqual(response.status_code, 302)
		self.assertIn('/login/', response.url)

	def test_requires_get_method(self):
		"""Test that the view only accepts GET requests."""
		self.client.force_login(self.user)
		
		url = reverse('link-duplicate-bank-transaction', kwargs={'duplicate_transaction_id': self.duplicate_transaction.id})
		response = self.client.post(url)
		
		# Should return 405 Method Not Allowed
		self.assertEqual(response.status_code, 405)

	def test_missing_bank_transaction_parameter(self):
		"""Test that the view requires bank_transaction query parameter."""
		self.client.force_login(self.user)
		
		# Test without bank_transaction parameter
		url = reverse('link-duplicate-bank-transaction', kwargs={'duplicate_transaction_id': self.duplicate_transaction.id})
		response = self.client.get(url)
		
		# Should return 400 Bad Request
		self.assertEqual(response.status_code, 400)
		self.assertIn('bank_transaction parameter is required', response.content.decode())

	def test_invalid_duplicate_transaction_id(self):
		"""Test that the view handles invalid duplicate transaction ID."""
		self.client.force_login(self.user)
		
		url = reverse('link-duplicate-bank-transaction', kwargs={'duplicate_transaction_id': 99999})
		response = self.client.get(url, {'bank_transaction': self.original_transaction.id})
		
		# Should return 404 Not Found
		self.assertEqual(response.status_code, 404)

	def test_invalid_original_transaction_id(self):
		"""Test that the view handles invalid original transaction ID."""
		self.client.force_login(self.user)
		
		url = reverse('link-duplicate-bank-transaction', kwargs={'duplicate_transaction_id': self.duplicate_transaction.id})
		response = self.client.get(url, {'bank_transaction': '99999'})
		
		# Should return 404 Not Found
		self.assertEqual(response.status_code, 404)

	def test_successful_duplicate_linking(self):
		"""Test successful linking of duplicate transactions."""
		self.client.force_login(self.user)
		
		# Verify initial state
		self.assertIsNone(self.duplicate_transaction.duplicate_of)
		
		url = reverse('link-duplicate-bank-transaction', kwargs={'duplicate_transaction_id': self.duplicate_transaction.id})
		response = self.client.get(url, {'bank_transaction': self.original_transaction.id})
		
		# Should redirect successfully
		self.assertEqual(response.status_code, 302)
		
		# Verify the duplicate relationship was created
		self.duplicate_transaction.refresh_from_db()
		self.assertEqual(self.duplicate_transaction.duplicate_of, self.original_transaction)

	def test_redirect_to_original_transaction_by_default(self):
		"""Test that the view redirects to the original transaction detail page by default."""
		self.client.force_login(self.user)
		
		url = reverse('link-duplicate-bank-transaction', kwargs={'duplicate_transaction_id': self.duplicate_transaction.id})
		response = self.client.get(url, {'bank_transaction': self.original_transaction.id})
		
		# Should redirect to the original transaction detail page
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, f'/finances/bank_transactions/{self.original_transaction.id}')

	def test_custom_redirect_url(self):
		"""Test that the view respects custom redirect-to parameter."""
		self.client.force_login(self.user)
		
		custom_redirect = '/custom/redirect/path/'
		url = reverse('link-duplicate-bank-transaction', kwargs={'duplicate_transaction_id': self.duplicate_transaction.id})
		response = self.client.get(url, {
			'bank_transaction': self.original_transaction.id,
			'redirect-to': custom_redirect
		})
		
		# Should redirect to the custom URL
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, custom_redirect)

	def test_linking_transaction_to_itself(self):
		"""Test linking a transaction to itself should return 400 Bad Request."""
		self.client.force_login(self.user)
		
		url = reverse('link-duplicate-bank-transaction', kwargs={'duplicate_transaction_id': self.duplicate_transaction.id})
		response = self.client.get(url, {'bank_transaction': self.duplicate_transaction.id})
		
		# Should return 400 Bad Request
		self.assertEqual(response.status_code, 400)
		self.assertIn('A transaction cannot be set as a duplicate of itself', response.content.decode())
		
		# Verify no relationship was created
		self.duplicate_transaction.refresh_from_db()
		self.assertIsNone(self.duplicate_transaction.duplicate_of)

	def test_relinking_already_linked_transaction(self):
		"""Test relinking a transaction that's already linked should return 400 Bad Request."""
		self.client.force_login(self.user)
		
		# Create a third transaction to attempt linking to
		third_transaction = BankTransaction.objects.create(
			name='Third Transaction',
			date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account
		)
		
		# First link duplicate to original
		self.duplicate_transaction.duplicate_of = self.original_transaction
		self.duplicate_transaction.save()
		
		# Now try to link duplicate to third transaction
		url = reverse('link-duplicate-bank-transaction', kwargs={'duplicate_transaction_id': self.duplicate_transaction.id})
		response = self.client.get(url, {'bank_transaction': third_transaction.id})
		
		# Should return 400 Bad Request
		self.assertEqual(response.status_code, 400)
		self.assertIn('Transaction is already marked as a duplicate of another transaction', response.content.decode())
		
		# Verify the duplicate relationship was not changed
		self.duplicate_transaction.refresh_from_db()
		self.assertEqual(self.duplicate_transaction.duplicate_of, self.original_transaction)

	def test_transaction_saves_after_linking(self):
		"""Test that the transaction is properly saved after linking."""
		self.client.force_login(self.user)
		
		url = reverse('link-duplicate-bank-transaction', kwargs={'duplicate_transaction_id': self.duplicate_transaction.id})
		response = self.client.get(url, {'bank_transaction': self.original_transaction.id})
		
		# Should redirect successfully
		self.assertEqual(response.status_code, 302)
		
		# Verify the transaction was saved (check database state)
		saved_transaction = BankTransaction.objects.get(id=self.duplicate_transaction.id)
		self.assertEqual(saved_transaction.duplicate_of, self.original_transaction)