import csv

import tablib
from django.db import models

from core.models.bank_transaction import BankTransaction

UNICREDIT_BANK_ACCOUNT_CSV_EXPORT = 'UNICREDIT_BANK_ACCOUNT_CSV_EXPORT'


class BankFileImport(models.Model):
	class FileType(models.TextChoices):
		UNICREDIT_BANK_ACCOUNT_CSV_EXPORT = 'UNICREDIT_BANK_ACCOUNT_CSV_EXPORT'
		FINECO_BANK_ACCOUNT_XLSX_EXPORT = 'FINECO_BANK_ACCOUNT_XLSX_EXPORT'
		UNICREDIT_DEBIT_CARD_CSV_EXPORT = 'UNICREDIT_DEBIT_CARD_CSV_EXPORT'
		CREDEM_CSV_EXPORT = 'CREDEM_CSV_EXPORT'

	id = models.AutoField(primary_key=True)
	file_type = models.CharField(
		max_length=255, choices=FileType
	)
	bank_file = models.FileField(upload_to='uploads/')
	import_date = models.DateTimeField(auto_now_add=True)


	class Meta:
		db_table = 'bank_file_imports'


	# Could the need for this "bank" property be a DB modeling smell? Maybe it makes more sense to link the import
	# to a bank account?
	@property
	def bank(self):
		if self.file_type == BankFileImport.FileType.CREDEM_CSV_EXPORT:
			return 'Credem'
		elif self.file_type == BankFileImport.FileType.UNICREDIT_BANK_ACCOUNT_CSV_EXPORT \
			or self.file_type == BankFileImport.FileType.UNICREDIT_DEBIT_CARD_CSV_EXPORT:
			return 'Unicredit'
		return 'Fineco'



	def __str__(self):
		return f'{self.import_date} - {self.file_type}'

	def _find_fineco_header_row(self):
		"""
		Dynamically find the row number where 'Data_Operazione' appears in the Fineco XLSX file.
		Returns the number of rows to skip before the header row.
		"""
		# Load the entire file without skipping any lines
		# Note: tablib automatically uses the first physical row as header (not shown in iteration)
		dataset = tablib.Dataset().load(self.bank_file, format='xlsx')

		# Check if Data_Operazione is already in the headers (first physical row)
		if dataset.headers and 'Data_Operazione' in dataset.headers:
			return 0  # No rows to skip, it's already the header

		# Search for the row containing 'Data_Operazione'
		# The index represents rows after the automatically-used header,
		# so we need to add 1 to get the correct skip_lines value
		for index, row in enumerate(dataset):
			if row and 'Data_Operazione' in row:
				return index + 1

		# If not found, return 0 (no rows to skip)
		return 0

	def get_file_rows(self):
		if self.file_type == BankFileImport.FileType.FINECO_BANK_ACCOUNT_XLSX_EXPORT:
			# Fineco exports an XLSX file with a variable number of header rows
			# Dynamically find how many rows to skip by locating 'Data_Operazione'
			rows_to_skip = self._find_fineco_header_row()
			all_rows = tablib.Dataset().load(self.bank_file, format='xlsx', skip_lines=rows_to_skip).dict

			# Filter out rows where Data_Operazione is not a valid date
			# (Fineco uses "-" for authorized but not yet processed transactions)
			return [row for row in all_rows if row.get('Data_Operazione') != '-']
		else:
			with open(self.bank_file.path, 'r') as text_mode_file:
				if self.file_type == BankFileImport.FileType.CREDEM_CSV_EXPORT:
					# Skip the first 7 lines for Credem files as they have a different format
					for _ in range(11):
						next(text_mode_file)
				f = csv.DictReader(text_mode_file, delimiter=';')
				return [i for i in f]

	def save(self, *args, **kwargs):
		imported = super().save(*args, **kwargs)

		strategy_mapping = {
			BankFileImport.FileType.UNICREDIT_BANK_ACCOUNT_CSV_EXPORT: BankTransaction.from_unicredit_bank_account_csv_row,
			BankFileImport.FileType.UNICREDIT_DEBIT_CARD_CSV_EXPORT: BankTransaction.from_unicredit_debit_card_csv_row,
			BankFileImport.FileType.FINECO_BANK_ACCOUNT_XLSX_EXPORT: BankTransaction.from_fineco_bank_account_xslx_row,
			BankFileImport.FileType.CREDEM_CSV_EXPORT: BankTransaction.from_credem_csv_row,
		}

		file_parsing_strategy = strategy_mapping.get(self.file_type, None)

		# When saving, we want it to create many single transactions entries as per file (if a strategy is defined)
		rows = self.get_file_rows()
		bank_transactions = [file_parsing_strategy(row, self) for row in rows]

		# Given that we have a unique constraint based on SQL based on name, date and amount, the already-imported
		# transactions will trigger an error. However, by using `ignore_conflicts`, we can just simulate a behavior where
		# the duplicates are just skipped
		BankTransaction.objects.bulk_create(bank_transactions, ignore_conflicts=True)
		return imported
