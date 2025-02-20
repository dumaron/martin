from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime
from finances.utils import fix_unicredit_floating_point
from .bank_file_import import BankFileImport

User = get_user_model()

class BankExpense(models.Model):
   id = models.AutoField(primary_key=True)
   file_import = models.ForeignKey(BankFileImport, on_delete=models.CASCADE)
   name = models.CharField(max_length=1024)
   date = models.DateField()
   amount = models.DecimalField(max_digits=10, decimal_places=2)
   user = models.ForeignKey(User, on_delete=models.CASCADE)
   ynab_transaction_id = models.CharField(max_length=256, null=True, blank=True)
   paired_on = models.DateTimeField(null=True, blank=True)
   snoozed_on = models.DateTimeField(null=True, blank=True)

   class Meta:
      constraints = models.UniqueConstraint('name', 'date', 'amount', name='expense-uniqueness-name-date-amount'),

   @staticmethod
   def from_unicredit_bank_account_csv_row(row, user, file_import):
      return BankExpense(
         name=row['Descrizione'].strip(),
         amount=fix_unicredit_floating_point(row['Importo (EUR)']),
         user=user,
         date=datetime.strptime(row['Data Registrazione'], '%d.%m.%Y'),
         file_import=file_import
      )

   @staticmethod
   def from_unicredit_debit_card_csv_row(row, user, file_import):
      return BankExpense(
         name=row['Descrizione'].strip(),
         amount=fix_unicredit_floating_point(row['Importo']),
         user=user,
         date=datetime.strptime(row['Data Registrazione'], '%d/%m/%Y'),
         file_import=file_import
      )

   @staticmethod
   def from_fineco_bank_account_xslx_row(row, user, file_import):
      return BankExpense(
         name=row['Descrizione_Completa'].strip(),
         amount=float(row['Entrate'] or 0) + float(row['Uscite'] or 0),
         user=user,
         date=datetime.strptime(row['Data'], '%d/%m/%Y'),
         file_import=file_import
      )

   def __str__(self):
      return self.name