from datetime import datetime

from django.db.models import Max
from core.adapters.ynab import get_uncleared_expenses
from core.models import YnabTransaction, YnabImport


def sync_ynab_transactions(partial=False) -> None:
   """
   Sync YNAB transactions with local database using last import's server knowledge to get only new changes to
   transactions
   """

   last_server_knowledge = (
      YnabImport.objects.aggregate(Max('server_knowledge'))['server_knowledge__max'] or 0 if partial else 0
   )

   result = get_uncleared_expenses(last_server_knowledge)
   transactions = result.transactions
   new_server_knowledge = result.server_knowledge

   ynab_import = YnabImport(execution_datetime=datetime.now(), server_knowledge=new_server_knowledge)
   ynab_import.save()

   for t in transactions:
      YnabTransaction.objects.update_or_create(
         id=t.id,
         defaults={
            'date': datetime.strptime(t.date, '%Y-%m-%d').date(),
            'amount': t.amount / 1000,
            'memo': t.memo,
            'cleared': t.cleared,
            'approved': t.approved,
            'flag_color': t.flag_color,
            'flag_name': t.flag_name,
            'account_id': t.account_id,
            'payee_id': t.payee_id,
            'category_id': t.category_id,
            'transfer_account_id': t.transfer_account_id,
            'transfer_transaction_id': t.transfer_transaction_id,
            'matched_transaction_id': t.matched_transaction_id,
            'import_id': t.import_id,
            'debt_transaction_type': t.debt_transaction_type,
            'deleted': t.deleted,
            'local_import': ynab_import,
         },
      )
