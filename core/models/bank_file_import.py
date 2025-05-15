import csv

import tablib
from django.db import models

from core.models import BankTransaction

UNICREDIT_BANK_ACCOUNT_CSV_EXPORT = 'UNICREDIT_BANK_ACCOUNT_CSV_EXPORT'


class BankFileImport(models.Model):
   class FileType(models.TextChoices):
      UNICREDIT_BANK_ACCOUNT_CSV_EXPORT = 'UNICREDIT_BANK_ACCOUNT_CSV_EXPORT'
      FINECO_BANK_ACCOUNT_XSLX_EXPORT = 'FINECO_BANK_ACCOUNT_XLSX_EXPORT'
      UNICREDIT_DEBIT_CARD_CSV_EXPORT = 'UNICREDIT_DEBIT_CARD_CSV_EXPORT'
      CREDEM_CSV_EXPORT = 'CREDEM_CSV_EXPORT'

   id = models.AutoField(primary_key=True)
   file_name = models.CharField(max_length=255)
   file_type = models.CharField(max_length=255, choices=FileType, default=FileType.UNICREDIT_BANK_ACCOUNT_CSV_EXPORT)
   bank_file = models.FileField(upload_to='uploads/')
   import_date = models.DateTimeField(auto_now_add=True)

   class Meta:
      db_table = 'bank_file_imports'

   def __str__(self):
      return f'{self.import_date} - {self.file_type}'


   def get_file_rows(self):
      if self.file_type == BankFileImport.FileType.FINECO_BANK_ACCOUNT_XSLX_EXPORT:
         # Fineco exports an XSLX file, so it need a different loader than the CSV one
         return tablib.Dataset().load(self.bank_file, format='xlsx', skip_lines=6).dict
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
         BankFileImport.FileType.FINECO_BANK_ACCOUNT_XSLX_EXPORT: BankTransaction.from_fineco_bank_account_xslx_row,
         BankFileImport.FileType.CREDEM_CSV_EXPORT: BankTransaction.from_credem_csv_row,
      }

      file_parsing_strategy = strategy_mapping.get(self.file_type, None)

      # When saving, we want it to create many single expense entries as per file (if a strategy is defined)
      rows = self.get_file_rows()
      expenses = [file_parsing_strategy(row, self) for row in rows]

      # Given that we have a unique constraint based on SQL based on name, date and amount, the already-imported
      # expenses will trigger an error. However, by using `ignore_conflicts`, we can just simulate a behaviour where
      # the duplicates are just skipped
      BankTransaction.objects.bulk_create(expenses, ignore_conflicts=True)
      return imported
