from datetime import datetime
import re

from django.db import models


def fix_italian_floating_point(string):
	return string.replace('.', '').replace(',', '.')


def clean_description(name):
	return ' '.join(name.split())


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
	name = models.CharField(max_length=1024) # TODO rename to description

	# Date attribute represents the closest available date to when the transaction was made.
	# In the real world, bank transaction is linked to many dates:
	# - the day the transaction was made;
	# - the day the transaction was recorded within the bank system;
	# - the day used for money value reference;
	# - eventual dates written within the transaction description.
	#
	# Bank exports include a different combination of dates, so we need to be careful when matching transactions: while
	# only the event date is interesting when pairing with a YNAB entry, if an export does not include it (I'm looking at
	# you Credem), we need to match on other attributes.
	#
	# The ideal solution would have been to store all of them and then calculate the best depending on the entry source.
	# However, I realized the limit imposed by having only a single date field in this data model too late. Now I cannot
	# create all these columns without introducing a nullability that is required not by the data nature but by
	# retro-compatibility, and I don't like that. On top of that, I also want to keep the model simple whenever possible,
	# and having a single field containing the "best" I can do for a single transaction is not that bad after all.
	#
	# So this field is it: the best I can do to match the date the event triggering the transaction has happened. For
	# Fineco I have the "operation date", so everyone is happy. For Credem I have the booking datem which is usually 2/3
	# days later than when the transaction occurred. Unicredit is already just kept for archiving purposes right now, so
	# I don't remember, and I don't care.
	#
	# I will maybe add a tooltip on the UI when matching Credem transactions to remember myself that a perfect date match
	# when doing pairing for the shared account is very hard to occur.
	date = models.DateField()
	#
	#

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
			models.UniqueConstraint('name', 'date', 'amount', name='bank-transaction-uniqueness-name-date-amount'),
		)
		db_table = 'bank_transactions'

	@classmethod
	def from_fineco_bank_account_xslx_row(cls, row, file_import):
		return cls(
			name=clean_description(row['Descrizione_Completa']),
			amount=float(row['Entrate'] or 0) + float(row['Uscite'] or 0),
			date=row['Data_Operazione'],
			file_import=file_import,
			bank_account_id=FINECO_BANK_ACCOUNT_ID,
		)

	@classmethod
	def from_credem_csv_row(cls, row, file_import):
		return cls(
			name=clean_description(row['Descrizione:']),
			amount=float(fix_italian_floating_point(row['Importo']) or 0),
			date=datetime.strptime(row['Data contabile'], '%d/%m/%Y'), # Unfortunately only booking date from Credem
			file_import=file_import,
			bank_account_id=CREDEM_BANK_ACCOUNT_ID,
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

	def get_description_suggestions(self):
		"""
		Returns a list of suggestions based on the description
		"""
		suggestions = [
			('AMZ', 'It l12312312')
		]

		regex_based_hints = [
			('AMZ', 'It l'),
			(re.escape('*2492'), 'Performed using Federica\'s card'),
		]

		for regex, explanation in regex_based_hints:
			if match := re.search(regex, self.name):
				suggestions.append((match.group(0), explanation))


		# Then add one related to dates

		return suggestions


	def __str__(self):
		return self.name
