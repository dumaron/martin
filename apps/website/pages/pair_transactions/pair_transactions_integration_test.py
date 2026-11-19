from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import BankAccount, BankFileImport, BankTransaction


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
