from django.db import models
from datetime import datetime
from ..utils.unicredit import fix_unicredit_floating_point
from .bank_file_import import BankFileImport

class BankExpense(models.Model):
   id = models.AutoField(primary_key=True)
   file_import = models.ForeignKey(BankFileImport, on_delete=models.CASCADE)
   name = models.CharField(max_length=1024)
   date = models.DateField()
   amount = models.DecimalField(max_digits=10, decimal_places=2)
   ynab_transaction_id = models.CharField(max_length=256, null=True, blank=True)
   paired_on = models.DateTimeField(null=True, blank=True)
   snoozed_on = models.DateTimeField(null=True, blank=True)

   class Meta:
      constraints = models.UniqueConstraint('name', 'date', 'amount', name='expense-uniqueness-name-date-amount'),
      db_table = 'bank_expenses'

   @staticmethod
   def from_unicredit_bank_account_csv_row(row, file_import):
      return BankExpense(
         name=row['Descrizione'].strip(),
         amount=fix_unicredit_floating_point(row['Importo (EUR)']),
         date=datetime.strptime(row['Data Registrazione'], '%d.%m.%Y'),
         file_import=file_import
      )

   @staticmethod
   def from_unicredit_debit_card_csv_row(row, file_import):
      return BankExpense(
         name=row['Descrizione'].strip(),
         amount=fix_unicredit_floating_point(row['Importo']),
         date=datetime.strptime(row['Data Registrazione'], '%d/%m/%Y'),
         file_import=file_import
      )

   @staticmethod
   def from_fineco_bank_account_xslx_row(row, file_import):
      return BankExpense(
         name=row['Descrizione_Completa'].strip(),
         amount=float(row['Entrate'] or 0) + float(row['Uscite'] or 0),
         date=datetime.strptime(row['Data'], '%d/%m/%Y'),
         file_import=file_import
      )

   def __str__(self):
      return self.name
