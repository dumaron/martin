from django.db import models
from core.integrations.file_reader import get_file_rows

class BankFileImport(models.Model):
   class FileType(models.TextChoices):
      UNICREDIT_BANK_ACCOUNT_CSV_EXPORT = 'UNICREDIT_BANK_ACCOUNT_CSV_EXPORT'
      FINECO_BANK_ACCOUNT_XSLX_EXPORT = 'FINECO_BANK_ACCOUNT_XLSX_EXPORT'
      UNICREDIT_DEBIT_CARD_CSV_EXPORT = 'UNICREDIT_DEBIT_CARD_CSV_EXPORT'

   id = models.AutoField(primary_key=True)
   file_name = models.CharField(max_length=255)
   file_type = models.CharField(max_length=255, choices=FileType, default=FileType.UNICREDIT_BANK_ACCOUNT_CSV_EXPORT)
   bank_file = models.FileField(upload_to='uploads/')
   import_date = models.DateTimeField(auto_now_add=True)

   class Meta:
      db_table = 'bank_file_imports'

   def __str__(self):
      return self.file_name

   def save(self, *args, **kwargs):
      imported = super().save(*args, **kwargs)

      file_parsing_strategy = None
      if self.file_type == BankFileImport.FileType.UNICREDIT_BANK_ACCOUNT_CSV_EXPORT:
         from .bank_expense import BankExpense
         file_parsing_strategy = BankExpense.from_unicredit_bank_account_csv_row
      elif self.file_type == BankFileImport.FileType.UNICREDIT_DEBIT_CARD_CSV_EXPORT:
         from .bank_expense import BankExpense
         file_parsing_strategy = BankExpense.from_unicredit_debit_card_csv_row
      elif self.file_type == BankFileImport.FileType.FINECO_BANK_ACCOUNT_XSLX_EXPORT:
         from .bank_expense import BankExpense
         file_parsing_strategy = BankExpense.from_fineco_bank_account_xslx_row

      if file_parsing_strategy is None:
         # not yet implemented, nothing to do
         return imported

      # When saving, we want it also to create many single expense entries as per file
      rows = get_file_rows(self.bank_file, self.file_type)
      expenses = [file_parsing_strategy(row, self) for row in rows]

      # Given that we have a unique constraint based on SQL based on name, date and amount, the already-imported
      # expenses will trigger an error. However, by using `ignore_conflicts`, we can just simulate a behaviour where
      # the duplicates are just skipped
      from .bank_expense import BankExpense
      BankExpense.objects.bulk_create(expenses, ignore_conflicts=True)
      return imported
