import datetime as dt
import re
from datetime import datetime

from django.db import models
from django.db.models.functions import Coalesce

from core.models.bank_transaction_description_hint import BankTransactionDescriptionHint
from core.utils.fp import first_or_none, last, lfilter, lmap, pipe

DATE_D_M_Y = re.compile(r'(?<![\d/])(\d{1,2})/(\d{1,2})/(\d{4}|\d{2})(?![\d/])')
TIME_HH_MM = re.compile(r'(?<![\d:])(?:[01]\d|2[0-3]):[0-5]\d(?![\d:])')
MAX_TIME_FROM_TRANSACTION_TO_BOOKING = dt.timedelta(days=60)

type DateInDescription = tuple[str, dt.date]


def fix_italian_floating_point(string):
	return string.replace('.', '').replace(',', '.')


def clean_description(description):
	return ' '.join(description.split())


def to_date_in_description(match: re.Match) -> DateInDescription | None:
	day, month, year = map(int, match.groups())
	try:
		return match.group(0), dt.date(year if year > 99 else 2000 + year, month, day)
	except ValueError:
		return None


def get_part_of_day(time):
	if 6 <= time.hour < 12:
		return 'Morning'
	if 12 <= time.hour < 18:
		return 'Afternoon'
	if 18 <= time.hour < 22:
		return 'Evening'
	return 'Night'


# I'm not happy with this approach, but it is a good compromise between creating a "proper" DB structure, which is
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
	# The booking date is stored as it comes from the exports, and it is empty when the export does not include it: the
	# nullability is required by the data nature. Both Fineco ("Data_Operazione", despite its name) and Credem give me
	# the booking date, which is usually 2/3 days later than when the transaction occurred. Unicredit is just kept for
	# archiving purposes, and its exports had the booking date ("Data Registrazione").
	# No export includes the transaction date: it is filled with the date written within the description, if any.
	# The value date is not stored, as I have no use for it.
	#
	# The `date` attribute represents the closest available date to when the transaction was made: the best I can do to
	# match the date the event triggering the transaction has happened. It is calculated by the database from the dates
	# above, and having a single field containing the "best" I can do for a single transaction is not that bad after all.
	#
	# I will maybe add a tooltip on the UI when matching Credem transactions to remind myself that a perfect date match
	# when doing pairing for the shared account is very hard to occur.
	transaction_date = models.DateField(null=True, blank=True)
	booking_date = models.DateField(null=True, blank=True)
	date = models.GeneratedField(
		expression=Coalesce('transaction_date', 'booking_date'),
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
				condition=models.Q(transaction_date__isnull=False) | models.Q(booking_date__isnull=False),
				name='bank-transaction-has-a-date',
			),
		)
		db_table = 'bank_transactions'

	@staticmethod
	def find_dates_in_description(description: str) -> list[DateInDescription]:
		return pipe(
			DATE_D_M_Y.finditer(description),
			lmap(to_date_in_description),
			lfilter(lambda found: found is not None),
		)

	@staticmethod
	def find_transaction_date_in_description(description: str, booking_date: dt.date) -> dt.date | None:
		def is_plausible(date: dt.date) -> bool:
			return dt.timedelta(0) <= booking_date - date <= MAX_TIME_FROM_TRANSACTION_TO_BOOKING

		return pipe(
			BankTransaction.find_dates_in_description(description),
			lmap(last),
			lfilter(is_plausible),
			first_or_none,
		)

	@classmethod
	def from_fineco_bank_account_xslx_row(cls, row, file_import):
		description = clean_description(row['Descrizione_Completa'])
		booking_date = row['Data_Operazione'].date()

		return cls(
			description=description,
			amount=float(row['Entrate'] or 0) + float(row['Uscite'] or 0),
			transaction_date=cls.find_transaction_date_in_description(description, booking_date),
			booking_date=booking_date,
			file_import=file_import,
			bank_account_id=FINECO_BANK_ACCOUNT_ID,
		)

	@classmethod
	def from_credem_csv_row(cls, row, file_import):
		description = clean_description(row['Descrizione:'])
		# Unfortunately, only booking date from Credem
		booking_date = datetime.strptime(row['Data contabile'], '%d/%m/%Y').date()

		return cls(
			description=description,
			amount=float(fix_italian_floating_point(row['Importo']) or 0),
			transaction_date=cls.find_transaction_date_in_description(description, booking_date),
			booking_date=booking_date,
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
		Find potential duplicate bank transactions: already paired ones with the same amount and date.
		Bank exports are unreliable: many times they change description text for the same transaction between two exports,
		making matching unstable.
		"""
		return (
			BankTransaction.objects.filter(amount=self.amount, date=self.date, paired_on__isnull=False)
			.exclude(id=self.id)
			.first()
		)

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
		if self.transaction_date:
			text_by_date = {date: text for text, date in BankTransaction.find_dates_in_description(self.description)}
			date_match = text_by_date.get(self.transaction_date, self.transaction_date)
			matched_hints.append((date_match, datetime.strftime(self.transaction_date, '%A %d/%m/%y')))

		if operation_time := self.get_operation_time_with_description():
			matched_hints.append((operation_time.strftime('%H:%M'), get_part_of_day(operation_time)))

		return matched_hints

	def __str__(self):
		return self.description
