from datetime import datetime

from django.db import models


def fix_italian_floating_point(string):
	return string.replace('.', '').replace(',', '.')

# I'm not happy about this approach, but it is a good compromise between creating a "proper" DB structure, which is
# overkill and unnecessarily complex for my needs, and hard-coding too much stuff. Here I insert into code the IDs of
# the three bank accounts I have on the database. Given that I use a clone of production DB for local development, and
# that I don't change bank accounts often, I can rely on these values being stable enough.
# I hope to discover a more elegant solution with time.
UNICREDIT_BANK_ACCOUNT_ID = 1
FINECO_BANK_ACCOUNT_ID = 2
CREDEM_BANK_ACCOUNT_ID = 3


class BankTransaction(models.Model):
	id = models.AutoField(primary_key=True)
	file_import = models.ForeignKey('BankFileImport', on_delete=models.CASCADE)
	name = models.CharField(max_length=1024)
	date = models.DateField()
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	ynab_transaction_id = models.CharField(max_length=256, null=True, blank=True)
	paired_on = models.DateTimeField(null=True, blank=True)
	snoozed_on = models.DateTimeField(null=True, blank=True)

	# The bank account this expense is coming from.
	bank_account = models.ForeignKey('BankAccount', on_delete=models.PROTECT)

	class Meta:
		constraints = (
			models.UniqueConstraint('name', 'date', 'amount', name='expense-uniqueness-name-date-amount'),
		)
		db_table = 'bank_transactions'

	@staticmethod
	def from_unicredit_bank_account_csv_row(row, file_import):
		return BankTransaction(
			name=row['Descrizione'].strip(),
			amount=fix_italian_floating_point(row['Importo (EUR)']),
			date=datetime.strptime(row['Data Registrazione'], '%d.%m.%Y'),
			file_import=file_import,
			bank_account_id=UNICREDIT_BANK_ACCOUNT_ID,
		)

	@staticmethod
	def from_unicredit_debit_card_csv_row(row, file_import):
		return BankTransaction(
			name=row['Descrizione'].strip(),
			amount=fix_italian_floating_point(row['Importo']),
			date=datetime.strptime(row['Data Registrazione'], '%d/%m/%Y'),
			file_import=file_import,
			bank_account_id=UNICREDIT_BANK_ACCOUNT_ID,
		)

	@staticmethod
	def from_fineco_bank_account_xslx_row(row, file_import):
		return BankTransaction(
			name=row['Descrizione_Completa'].strip(),
			amount=float(row['Entrate'] or 0) + float(row['Uscite'] or 0),
			date=datetime.strptime(row['Data'], '%d/%m/%Y'),
			file_import=file_import,
			bank_account_id=FINECO_BANK_ACCOUNT_ID,
		)

	@staticmethod
	def from_credem_csv_row(row, file_import):
		return BankTransaction(
			name=row['Descrizione:'],
			amount=float(fix_italian_floating_point(row['Importo']) or 0),
			date=datetime.strptime(row['Data contabile'], '%d/%m/%Y'),
			file_import=file_import,
			bank_account_id=CREDEM_BANK_ACCOUNT_ID,
		)

	def __str__(self):
		return self.name
