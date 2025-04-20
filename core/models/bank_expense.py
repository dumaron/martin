from datetime import datetime

from django.db import models


def fix_italian_floating_point(string):
	return string.replace('.', '').replace(',', '.')


class BankExpense(models.Model):
	id = models.AutoField(primary_key=True)
	file_import = models.ForeignKey('BankFileImport', on_delete=models.CASCADE)
	name = models.CharField(max_length=1024)
	date = models.DateField()
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	ynab_transaction_id = models.CharField(max_length=256, null=True, blank=True)
	paired_on = models.DateTimeField(null=True, blank=True)
	snoozed_on = models.DateTimeField(null=True, blank=True)

	# Tells if the import is from a personal account (Unicredit, Fineco) or a shared one (Credem)
	personal_account = models.BooleanField(default=True)

	class Meta:
		constraints = (
			models.UniqueConstraint('name', 'date', 'amount', name='expense-uniqueness-name-date-amount'),
		)
		db_table = 'bank_expenses'

	@staticmethod
	def from_unicredit_bank_account_csv_row(row, file_import):
		return BankExpense(
			name=row['Descrizione'].strip(),
			amount=fix_italian_floating_point(row['Importo (EUR)']),
			date=datetime.strptime(row['Data Registrazione'], '%d.%m.%Y'),
			personal_account=file_import.personal_account,
			file_import=file_import,
		)

	@staticmethod
	def from_unicredit_debit_card_csv_row(row, file_import):
		return BankExpense(
			name=row['Descrizione'].strip(),
			amount=fix_italian_floating_point(row['Importo']),
			date=datetime.strptime(row['Data Registrazione'], '%d/%m/%Y'),
			personal_account=file_import.personal_account,
			file_import=file_import,
		)

	@staticmethod
	def from_fineco_bank_account_xslx_row(row, file_import):
		return BankExpense(
			name=row['Descrizione_Completa'].strip(),
			amount=float(row['Entrate'] or 0) + float(row['Uscite'] or 0),
			date=datetime.strptime(row['Data'], '%d/%m/%Y'),
			personal_account=file_import.personal_account,
			file_import=file_import,
		)

	@staticmethod
	def from_credem_csv_row(row, file_import):
		return BankExpense(
			name=row['Descrizione:'],
			amount=float(fix_italian_floating_point(row['Importo']) or 0),
			date=datetime.strptime(row['Data contabile'], '%d/%m/%Y'),
			personal_account=file_import.personal_account,  # Should be always false as we only have a Credem shared account
			file_import=file_import,
		)

	def __str__(self):
		return self.name
