from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import BankAccount, BankFileImport, BankTransaction
from core.tests.base import FileCleanupTestCase


class LinkDuplicateBankTransactionViewTest(FileCleanupTestCase):
	"""Test the link_duplicate_bank_transaction view."""

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
				file_type=BankFileImport.FileType.CREDEM_CSV_EXPORT, bank_file=mock_file
			)

		# Create test transactions
		self.original_transaction = BankTransaction.objects.create(
			description='Original Transaction',
			booking_date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		self.duplicate_transaction = BankTransaction.objects.create(
			description='Duplicate Transaction',
			booking_date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

	def test_requires_login(self):
		"""A request without login is redirected to the login page."""
		url = reverse('pair_transactions_page.actions.link_duplicate_bank_transactions')
		response = self.client.post(
			url,
			{
				'bank_transaction_id': self.original_transaction.id,
				'target_bank_transaction_id': self.duplicate_transaction.id,
			},
		)

		# Should redirect to login
		self.assertEqual(response.status_code, 302)
		self.assertIn('/accounts/login/', response.url)

	def test_requires_post_method(self):
		"""A GET request is refused with 405 Method Not Allowed."""
		self.client.force_login(self.user)

		url = reverse('pair_transactions_page.actions.link_duplicate_bank_transactions')
		response = self.client.get(url)

		# Should return 405 Method Not Allowed
		self.assertEqual(response.status_code, 405)

	def test_invalid_duplicate_transaction_id(self):
		"""An unknown duplicate transaction id answers 404."""
		self.client.force_login(self.user)

		url = reverse('pair_transactions_page.actions.link_duplicate_bank_transactions')
		response = self.client.post(
			url, {'bank_transaction_id': 99999, 'target_bank_transaction_id': self.duplicate_transaction.id}
		)

		# Should return 404 Not Found
		self.assertEqual(response.status_code, 404)

	def test_invalid_target_transaction_id(self):
		"""An unknown target transaction id answers 404."""
		self.client.force_login(self.user)

		url = reverse('pair_transactions_page.actions.link_duplicate_bank_transactions')
		response = self.client.post(
			url, {'bank_transaction_id': self.original_transaction.id, 'target_bank_transaction_id': 99999}
		)

		# Should return 404 Not Found
		self.assertEqual(response.status_code, 404)

	def test_successful_duplicate_linking(self):
		"""Linking two transactions marks the target as a duplicate of the other one and redirects."""
		self.client.force_login(self.user)

		# Verify initial state
		self.assertIsNone(self.duplicate_transaction.duplicate_of)

		url = reverse('pair_transactions_page.actions.link_duplicate_bank_transactions')
		response = self.client.post(
			url,
			{
				'bank_transaction_id': self.original_transaction.id,
				'target_bank_transaction_id': self.duplicate_transaction.id,
				'redirect-to': '/test-redirect/',
			},
		)

		# Should redirect successfully
		self.assertEqual(response.status_code, 302)

		# Verify the duplicate relationship was created
		# target_transaction becomes a duplicate of duplicate_transaction
		self.duplicate_transaction.refresh_from_db()
		self.assertEqual(self.duplicate_transaction.duplicate_of, self.original_transaction)

	def test_custom_redirect_url(self):
		"""After linking, the view redirects to the URL given in redirect-to."""
		self.client.force_login(self.user)

		custom_redirect = '/custom/redirect/path/'
		url = reverse('pair_transactions_page.actions.link_duplicate_bank_transactions')
		response = self.client.post(
			url,
			{
				'bank_transaction_id': self.original_transaction.id,
				'target_bank_transaction_id': self.duplicate_transaction.id,
				'redirect-to': custom_redirect,
			},
		)

		# Should redirect to the custom URL
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, custom_redirect)

	def test_linking_transaction_to_itself(self):
		"""Test linking a transaction to itself should return 400 Bad Request."""
		self.client.force_login(self.user)

		url = reverse('pair_transactions_page.actions.link_duplicate_bank_transactions')
		response = self.client.post(
			url,
			{
				'bank_transaction_id': self.duplicate_transaction.id,
				'target_bank_transaction_id': self.duplicate_transaction.id,
			},
		)

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
			description='Third Transaction',
			booking_date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# First link duplicate to original
		self.duplicate_transaction.duplicate_of = self.original_transaction
		self.duplicate_transaction.save()

		# Now try to link duplicate to third transaction (should fail)
		url = reverse('pair_transactions_page.actions.link_duplicate_bank_transactions')
		response = self.client.post(
			url,
			{'bank_transaction_id': third_transaction.id, 'target_bank_transaction_id': self.duplicate_transaction.id},
		)

		# Should return 400 Bad Request
		self.assertEqual(response.status_code, 400)
		self.assertIn(
			'Transaction is already marked as a duplicate of another transaction', response.content.decode()
		)

		# Verify the duplicate relationship was not changed
		self.duplicate_transaction.refresh_from_db()
		self.assertEqual(self.duplicate_transaction.duplicate_of, self.original_transaction)

	def test_transaction_saves_after_linking(self):
		"""After linking, the duplicate relationship is stored in the database."""
		self.client.force_login(self.user)

		url = reverse('pair_transactions_page.actions.link_duplicate_bank_transactions')
		response = self.client.post(
			url,
			{
				'bank_transaction_id': self.original_transaction.id,
				'target_bank_transaction_id': self.duplicate_transaction.id,
				'redirect-to': '/test-redirect/',
			},
		)

		# Should redirect successfully
		self.assertEqual(response.status_code, 302)

		# Verify the transaction was saved (check database state)
		saved_transaction = BankTransaction.objects.get(id=self.duplicate_transaction.id)
		self.assertEqual(saved_transaction.duplicate_of, self.original_transaction)


class PairingViewTest(FileCleanupTestCase):
	"""Test the pairing view."""

	def setUp(self):
		"""Set up test data."""
		# Create a test user and log in
		self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
		self.client.force_login(self.user)

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
				file_type=BankFileImport.FileType.CREDEM_CSV_EXPORT, bank_file=mock_file
			)

	def create_original_and_duplicate_transactions(self) -> None:
		# Create test transactions
		self.original_transaction = BankTransaction.objects.create(
			description='Original Transaction',
			booking_date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		self.duplicate_transaction = BankTransaction.objects.create(
			description='Duplicate Transaction',
			booking_date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
			duplicate_of=self.original_transaction,
		)

	def test_pairing_view_excludes_duplicates(self):
		"""Test that the pairing view excludes transactions marked as duplicates."""

		self.create_original_and_duplicate_transactions()

		# Get the pairing view for personal transactions
		url = reverse('pair_transactions_page.main_render', kwargs={'kind': 'personal'})
		response = self.client.get(url)

		# Should return 200 OK
		self.assertEqual(response.status_code, 200)

		# The view should show the original transaction, not the duplicate
		self.assertEqual(response.context['bank_transaction'], self.original_transaction)
		self.assertNotEqual(response.context['bank_transaction'], self.duplicate_transaction)

	def test_pairing_view_with_only_duplicates(self):
		"""Test that the pairing view shows empty when only duplicates exist."""

		self.create_original_and_duplicate_transactions()

		# Mark the original transaction as a duplicate too
		self.original_transaction.duplicate_of = self.duplicate_transaction
		self.original_transaction.save()

		# Get the pairing view for personal transactions
		url = reverse('pair_transactions_page.main_render', kwargs={'kind': 'personal'})
		response = self.client.get(url)

		# Should return 200 OK but show empty template
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'pair_transactions/pairing_empty.html')

	def test_pairing_view_shows_difflib_for_potential_duplicates(self):
		"""Test that the pairing view shows difflib output for potential duplicates."""

		# Create a main transaction (will be shown in pairing view)
		BankTransaction.objects.create(
			description='Main Transaction',
			booking_date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# Create a potential duplicate with slightly different description but same date/amount
		BankTransaction.objects.create(
			description='Slightly Different Transaction Name',
			booking_date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
			paired_on=timezone.now(),
		)

		# Get the pairing view for personal transactions
		url = reverse('pair_transactions_page.main_render', kwargs={'kind': 'personal'})
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

	def test_pairing_view_displays_potential_duplicate_widget_when_duplicate_exists(self):
		"""Test that pairing view displays potential duplicate widget when a duplicate exists."""

		# Create first transaction (this will be the one shown in pairing view since it's oldest)
		BankTransaction.objects.create(
			description='Current Transaction',
			booking_date=date(2024, 1, 14),  # Earlier date so it's shown first
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# Create a second transaction (potential duplicate with same date and amount)
		duplicate_transaction = BankTransaction.objects.create(
			description='Original Transaction',
			booking_date=date(2024, 1, 14),  # Same date for duplicate detection
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
			paired_on=timezone.now(),
		)

		# Get the pairing view
		response = self.client.get(reverse('pair_transactions_page.main_render', kwargs={'kind': 'personal'}))

		# Check that the response is successful
		self.assertEqual(response.status_code, 200)

		# Check that the potential duplicate warning is present in the HTML
		self.assertContains(response, 'Potential duplicate detected')
		# Check that the highlighted text appears (parts of "Original Transaction" will be highlighted)
		self.assertContains(response, 'Transaction')  # This part should appear unhighlighted
		self.assertContains(
			response, '<span style="background-color: #ffcccc'
		)  # Highlighting spans should be present

		# Check that the potential duplicate data is passed to the template
		self.assertIsNotNone(response.context['potential_duplicate'])
		# The current transaction should find the duplicate transaction
		self.assertEqual(response.context['potential_duplicate'], duplicate_transaction)

	def test_pairing_view_does_not_display_potential_duplicate_widget_when_no_duplicate(self):
		"""Test that pairing view does not display potential duplicate widget when no duplicate exists."""

		# Create only one transaction (no duplicate)
		BankTransaction.objects.create(
			description='Single Transaction',
			booking_date=date(2024, 1, 15),
			amount=Decimal('100.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# Get the pairing view
		response = self.client.get(reverse('pair_transactions_page.main_render', kwargs={'kind': 'personal'}))

		# Check that the response is successful
		self.assertEqual(response.status_code, 200)

		# Check that the potential duplicate warning is NOT present in the HTML
		self.assertNotContains(response, 'Potential duplicate detected')

		# Check that potential_duplicate is None in the context
		self.assertIsNone(response.context['potential_duplicate'])


class SnoozeBankTransactionTest(TestCase):
	def setUp(self):
		self.client.force_login(User.objects.create_user(username='tester'))
		self.bank_transaction = BankTransaction.objects.create(
			description='Ricarica carta di debito',
			amount=Decimal('-50.00'),
			booking_date=date(2026, 11, 2),
			file_import=BankFileImport.objects.bulk_create(
				[BankFileImport(file_type=BankFileImport.FileType.CREDEM_CSV_EXPORT, bank_file='uploads/export.csv')]
			)[0],
			bank_account=BankAccount.objects.create(
				name='Personal', iban='IT60X0542811101000000123456', personal=True
			),
		)
		self.url = reverse('pair_transactions_page.actions.snooze_bank_transaction')
		self.redirect_to = reverse('pair_transactions_page.main_render', kwargs={'kind': 'personal'})

	def test_snoozes_transaction(self):
		"""Snoozing with the fields the pairing page posts sets the snooze date and goes back to the given page."""
		response = self.client.post(
			self.url, {'bank_transaction_id': self.bank_transaction.id, 'redirect-to': self.redirect_to}
		)

		self.bank_transaction.refresh_from_db()
		self.assertIsNotNone(self.bank_transaction.snoozed_on)
		self.assertRedirects(response, self.redirect_to, fetch_redirect_response=False)

	def test_missing_id(self):
		"""Snoozing without a bank transaction id answers 400 and snoozes nothing."""
		response = self.client.post(self.url, {'redirect-to': self.redirect_to})

		self.bank_transaction.refresh_from_db()
		self.assertEqual(response.status_code, 400)
		self.assertIsNone(self.bank_transaction.snoozed_on)

	def test_non_numeric_id(self):
		"""Snoozing with a bank transaction id that is not a number answers 400 and snoozes nothing."""
		response = self.client.post(self.url, {'bank_transaction_id': 'abc', 'redirect-to': self.redirect_to})

		self.bank_transaction.refresh_from_db()
		self.assertEqual(response.status_code, 400)
		self.assertIsNone(self.bank_transaction.snoozed_on)

	def test_unknown_id(self):
		"""Snoozing a bank transaction that does not exist answers 404 and leaves the existing one unsnoozed."""
		response = self.client.post(self.url, {'bank_transaction_id': 999999, 'redirect-to': self.redirect_to})

		self.bank_transaction.refresh_from_db()
		self.assertEqual(response.status_code, 404)
		self.assertIsNone(self.bank_transaction.snoozed_on)
