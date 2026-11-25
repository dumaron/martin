from datetime import date

from django.test import SimpleTestCase

from core.models import BankTransaction


class FindDatesInDescriptionTest(SimpleTestCase):
	def test_returns_text_and_date(self):
		"""Every slash-separated date comes back with the text it was written as, in order of appearance."""
		self.assertEqual(
			BankTransaction.find_dates_in_description('Ins: 25/04/2024 11:05:42 Cau: Proforma nr. 23 del 24/04/2024'),
			[('25/04/2024', date(2024, 4, 25)), ('24/04/2024', date(2024, 4, 24))],
		)

	def test_skips_impossible_dates(self):
		"""A text shaped like a date that does not exist on the calendar is not returned."""
		self.assertEqual(BankTransaction.find_dates_in_description('Pagamento del 31/02/25'), [])

	def test_ignores_dotted_dates(self):
		"""Dates written with dots are not taken, as in Credem they are invoice dates."""
		self.assertEqual(BankTransaction.find_dates_in_description('BONIFICO A DEBITO FT N. 52 DEL 31.07.25'), [])


class FindTransactionDateInDescriptionTest(SimpleTestCase):
	def test_credem_card_payment(self):
		"""A Credem card payment gets the date written next to the payment time."""
		self.assertEqual(
			BankTransaction.find_transaction_date_in_description(
				'PAGAMENTO DEBINT PAGAMENTO CARTA DI DEBITO INTERNAZIONALE 537572******2965 -14/04/25-19:18 PAM PARMA -ITA',
				date(2025, 4, 16),
			),
			date(2025, 4, 14),
		)

	def test_fineco_card_payment(self):
		"""A Fineco card payment gets the date written after "Data operazione"."""
		self.assertEqual(
			BankTransaction.find_transaction_date_in_description(
				'Audible*3N9IV1543 Amzn.com/bill NJ Carta N. ***** 013 Data operazione 25/05/24', date(2024, 5, 27)
			),
			date(2024, 5, 25),
		)

	def test_single_digit_day_and_month(self):
		"""A date written with a single digit for the day or the month is read the same as a padded one."""
		self.assertEqual(
			BankTransaction.find_transaction_date_in_description(
				'Prelevamento Carta N ***** 201 Data operazione: 12/4/2025 Ora: 08:39', date(2025, 4, 14)
			),
			date(2025, 4, 12),
		)

	def test_first_plausible_date_wins(self):
		"""With more than one plausible date in the description, the first one is taken."""
		self.assertEqual(
			BankTransaction.find_transaction_date_in_description(
				'Ben: ROSSI Ins: 25/04/2024 11:05:42 Da: INTERNET Cau: Proforma nr. 23 del 24/04/2024', date(2024, 4, 25)
			),
			date(2024, 4, 25),
		)

	def test_skips_implausible_date_before_a_plausible_one(self):
		"""A date too far from the booking date is skipped, and a later plausible one is taken instead."""
		self.assertEqual(
			BankTransaction.find_transaction_date_in_description(
				'Rimborso sessione 22/12/23 accreditato il 20/03/24', date(2024, 3, 21)
			),
			date(2024, 3, 20),
		)

	def test_date_long_before_booking(self):
		"""A date more than 60 days before the booking date is not a transaction date."""
		self.assertIsNone(
			BankTransaction.find_transaction_date_in_description(
				'BONIFICO SEPA A: ROSSI PER: Bonifico per sessione 22/12/23', date(2024, 3, 19)
			)
		)

	def test_date_within_the_window(self):
		"""A date 41 days before the booking date is still taken."""
		self.assertEqual(
			BankTransaction.find_transaction_date_in_description(
				'Uniqlo Europe Ltd Ital Milano CAP IT Carta N. ***** 013 Data operazione 03/07/26', date(2026, 8, 13)
			),
			date(2026, 7, 3),
		)

	def test_date_after_booking(self):
		"""A date later than the booking date is not a transaction date."""
		self.assertIsNone(
			BankTransaction.find_transaction_date_in_description(
				'Pagamento rata scadenza 30/04/2024', date(2024, 4, 2)
			)
		)

	def test_date_of_a_law_reference(self):
		"""The date of the law quoted in the stamp duty description is not a transaction date."""
		self.assertIsNone(
			BankTransaction.find_transaction_date_in_description(
				'IMPOSTA BOLLO CONTO CORRENTE DPR642/72-DM24/5/2012', date(2024, 4, 2)
			)
		)

	def test_no_date(self):
		"""A description with no date gives no transaction date."""
		self.assertIsNone(
			BankTransaction.find_transaction_date_in_description(
				'Canone Mensile Conto Ottobre 2026', date(2026, 11, 5)
			)
		)
