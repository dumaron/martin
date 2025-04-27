from django.db import models

from core.models.ynab_account import YnabAccount
from core.models.ynab_budget import YnabBudget
from core.models.ynab_import import YnabImport


class YnabTransaction(models.Model):
   class ClearedStatuses(models.TextChoices):
      CLEARED = 'cleared'
      UNCLEARED = 'uncleared'
      RECONCILED = 'reconciled'

   class FlagColors(models.TextChoices):
      RED = 'red'
      ORANGE = 'orange'
      YELLOW = 'yellow'  # shared with Federica using the official ratio (70/30)
      GREEN = 'green'
      BLUE = 'blue'
      PURPLE = 'purple'

   class TransactionTypes(models.TextChoices):
      PAYMENT = 'payment'
      REFUND = 'refund'
      FEE = 'fee'
      INTEREST = 'interest'
      ESCROW = 'escrow'
      BALANCE_ADJUSTMENT = 'balanceAdjustment'
      CREDIT = 'credit'
      CHARGE = 'charge'

   id = models.CharField(primary_key=True, max_length=64)
   date = models.DateField()
   amount = models.FloatField()
   memo = models.CharField(null=True, blank=True, max_length=512)
   approved = models.BooleanField()
   cleared = models.CharField(choices=ClearedStatuses, max_length=10)
   flag_color = models.CharField(null=True, blank=True, choices=FlagColors, max_length=6)
   flag_name = models.CharField(null=True, blank=True, max_length=64)
   account = models.ForeignKey(YnabAccount, on_delete=models.CASCADE, null=True, blank=True)
   payee_id = models.UUIDField(null=True, blank=True)
   category_id = models.UUIDField(null=True, blank=True)
   transfer_account_id = models.UUIDField(null=True, blank=True)
   transfer_transaction_id = models.CharField(null=True, blank=True, max_length=64)
   matched_transaction_id = models.CharField(null=True, blank=True, max_length=64)
   import_id = models.CharField(null=True, blank=True, max_length=64)
   import_payee_name = models.CharField(null=True, blank=True, max_length=256)
   import_payee_original = models.CharField(null=True, blank=True, max_length=256)
   debt_transaction_type = models.CharField(null=True, blank=True, choices=TransactionTypes, max_length=17)
   deleted = models.BooleanField()
   local_import = models.ForeignKey(YnabImport, on_delete=models.CASCADE)
   budget = models.ForeignKey(YnabBudget, on_delete=models.CASCADE)

   def __str__(self):
      return f'{self.amount} {self.date} {self.memo}'

   class Meta:
      db_table = 'ynab_transactions'

   @classmethod
   def from_external_transaction(cls, external_transaction, local_import):
      return YnabTransaction(
         id=external_transaction.id,
         date=external_transaction.date,
         amount=external_transaction.amount,
         memo=external_transaction.memo,
         approved=external_transaction.approved,
         cleared=external_transaction.cleared,
         flag_color=external_transaction.flag_color,
         flag_name=external_transaction.flag_name,
         account_id=external_transaction.account_id,
         payee_id=external_transaction.payee_id,
         category_id=external_transaction.category_id,
         transfer_account_id=external_transaction.transfer_account_id,
         transfer_transaction_id=external_transaction.transfer_transaction_id,
         matched_transaction_id=external_transaction.matched_transaction_id,
         import_id=external_transaction.import_id,
         import_payee_name=external_transaction.import_payee_name,
         import_payee_original=external_transaction.import_payee_original,
         debt_transaction_type=external_transaction.debt_transaction_type,
         deleted=external_transaction.deleted,
         local_import=local_import
      )
