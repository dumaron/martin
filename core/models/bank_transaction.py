import datetime as dt
import re
from datetime import datetime

from django.db import models
from django.db.models.functions import Coalesce

from core.models.bank_transaction_description_hint import BankTransactionDescriptionHint

DATE_DD_MM_YY = re.compile(r'(?<![\d/])(?:0[1-9]|[12]\d|3[01])/(?:0[1-9]|1[0-2])/\d{2}(?![\d/])')
TIME_HH_MM = re.compile(r'(?<![\d:])(?:[01]\d|2[0-3]):[0-5]\d(?![\d:])')


def fix_italian_floating_point(string):
	return string.replace('.', '').replace(',', '.')


def clean_description(description):
	return ' '.join(description.split())


def get_part_of_day(time):
	if 6 <= time.hour < 12:
		return 'Morning'
	if 12 <= time.hour < 18:
		return 'Afternoon'
	if 18 <= time.hour < 22:
		return 'Evening'
	return 'Night'


# I'm not happy about this approach, but it is a good compromise between creating a "proper" DB structure, which is
# overkill and unnecessarily complex for my needs, and hard-coding too much stuff. Here I inserted into code the IDs of
# the two bank accounts I have on the database. Given that I use a clone of production DB for local development, and
# that I don't change bank accounts often, I can rely on these values being stable enough.
# I hope to discover a more elegant solution with time.
FINECO_BANK_ACCOUNT_ID = 2
CREDEM_BANK_ACCOUNT_ID = 3


class BankTransaction(models.Model):
	id = models.AutoField(primary_key=True)
	file_import = models.ForeignKey('BankFileImport', on_delete=models.CASCADE)
	description = models.CharField(max_length=1024)

	# In the real world, bank transaction is linked to many dates:
	# - the day the transaction was made (transaction date);
	# - the day the transaction was recorded within the bank system (booking date);
	# - the day used for money value reference (value date);
	# - eventual dates written within the transaction description.
	#
	# Bank exports include a different combination of dates, so we need to be careful when matching transactions: while
	# only the event date is interesting when pairing with a YNAB entry, if an export does not include it (I'm looking at
	# you Credem), we need to match on other attributes.
	#
	# The first three are stored as they come from the exports, and each one is empty when the export does not include
	# it: the nullability is required by the data nature. For Fineco I have the transaction date, so everyone is happy.
	# For Credem I have the booking date which is usually 2/3 days later than when the transaction occurred. Unicredit
	# is just kept for archiving purposes, and its exports had the booking date ("Data Registrazione").
	#
	# The `date` attribute represents the closest available date to when the transaction was made: the best I can do to
	# match the date the event triggering the transaction has happened. It is calculated by the database from the dates
	# above, and having a single field containing the "best" I can do for a single transaction is not that bad after all.
	#
	# I will maybe add a tooltip on the UI when matching Credem transactions to remind myself that a perfect date match
	# when doing pairing for the shared account is very hard to occur.
	transaction_date = models.DateField(null=True, blank=True)
	booking_date = models.DateField(null=True, blank=True)
	value_date = models.DateField(null=True, blank=True)
	date = models.GeneratedField(
		expression=Coalesce('transaction_date', 'booking_date', 'value_date'),
		output_field=models.DateField(),
		db_persist=True,
	)

	amount = models.DecimalField(max_digits=10, decimal_places=2)
	matched_ynab_transaction = models.ForeignKey(
		'YnabTransaction', null=True, blank=True, on_delete=models.CASCADE
	)
	paired_on = models.DateTimeField(null=True, blank=True)
	snoozed_on = models.DateTimeField(null=True, blank=True)

	# We consider "duplicate" bank transactions the ones that are the same transaction in the real world, but have a
	# slightly different description in the original bank exports. This is often caused by banks changing transaction
	# description from one import to another.
	# I want to link the two (or more??) transactions together, as it can be useful in the future to list all the
	# possible variations in the future.
	# I wonder if it could make sense to switch instead to an "alias" data model, where a transaction might have many
	# descriptions. Mah.
	duplicate_of = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

	# The bank account this transaction is coming from.
	bank_account = models.ForeignKey('BankAccount', on_delete=models.PROTECT)

	class Meta:
		constraints = (
			# I'm not sure this is correct. If I ever move to an "alias" approach where bank transactions are expected to
			# have different descriptions over time, then is there any need for this constraint? How am I supposed to avoid
			# duplicating transactions that have already been imported?
			models.UniqueConstraint(
				'description', 'date', 'amount', name='bank-transaction-uniqueness-description-date-amount'
			),
			models.CheckConstraint(
				condition=models.Q(transaction_date__isnull=False)
				| models.Q(booking_date__isnull=False)
				| models.Q(value_date__isnull=False),
				name='bank-transaction-has-a-date',
			),
		)
		db_table = 'bank_transactions'

	@classmethod
	def from_fineco_bank_account_xslx_row(cls, row, file_import):
		return cls(
			description=clean_description(row['Descrizione_Completa']),
			amount=float(row['Entrate'] or 0) + float(row['Uscite'] or 0),
			transaction_date=row['Data_Operazione'],
			file_import=file_import,
			bank_account_id=FINECO_BANK_ACCOUNT_ID,
		)

	@classmethod
	def from_credem_csv_row(cls, row, file_import):
		return cls(
			description=clean_description(row['Descrizione:']),
			amount=float(fix_italian_floating_point(row['Importo']) or 0),
			# Unfortunately, only booking date from Credem
			booking_date=datetime.strptime(row['Data contabile'], '%d/%m/%Y'),
			file_import=file_import,
			bank_account_id=CREDEM_BANK_ACCOUNT_ID,
		)

	@classmethod
	def search_paired_by_description(cls, query):
		search = (query or '').strip()
		if not search:
			return cls.objects.none()

		return (
			cls.objects.filter(description__icontains=search, matched_ynab_transaction__isnull=False)
			.select_related('matched_ynab_transaction__category')
			.order_by('-date', '-id')
		)

	def get_potential_duplicate(self):
		"""
		Find potential duplicate bank transactions with the same amount and date.
		Bank exports are unreliable: many times they change description text for the same transaction between two exports,
		making matching unstable.
		"""
		return (
			BankTransaction.objects.filter(amount=self.amount, date=self.date, paired_on__isnull=False)
			.exclude(id=self.id)
			.first()
		)

	def get_operation_date_with_description(self) -> dt.date | None:
		if self.transaction_date:
			return self.transaction_date

		if match := DATE_DD_MM_YY.search(self.description):
			return datetime.strptime(match.group(0), '%d/%m/%y').date()

		return None

	def get_operation_time_with_description(self) -> dt.time | None:
		if match := TIME_HH_MM.search(self.description):
			return datetime.strptime(match.group(0), '%H:%M').time()

		return None

	def get_description_hints(self):
		"""
		Returns a list of suggestions based on the description
		"""
		matched_hints = []

		regex_based_hints = BankTransactionDescriptionHint.objects.all()

		for potential_hint in regex_based_hints:
			if match := re.search(potential_hint.regex, self.description):
				matched_hints.append((match.group(0), potential_hint.hint))

		# There can be specific hints based on the bank account the transaction comes from
		operation_date = self.get_operation_date_with_description()
		if operation_date:
			date_text = operation_date.strftime('%d/%m/%y')
			date_match = date_text if date_text in DATE_DD_MM_YY.findall(self.description) else operation_date
			matched_hints.append((date_match, datetime.strftime(operation_date, '%A %d/%m/%y')))

		operation_time = self.get_operation_time_with_description()
		if operation_time:
			time_text = operation_time.strftime('%H:%M')
			time_match = time_text if time_text in TIME_HH_MM.findall(self.description) else operation_time
			matched_hints.append((time_match, get_part_of_day(operation_time)))

		return matched_hints

	def __str__(self):
		return self.description
