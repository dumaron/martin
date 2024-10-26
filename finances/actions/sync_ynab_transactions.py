from datetime import datetime

from django.db.models import Max
from ..adapters.ynab import YnabAdapter
from ..models import YnabTransaction, YnabImport


def sync_ynab_transactions(partial, user) -> None:
    last_server_knowledge = 0
    if partial:
        last_server_knowledge = YnabImport.objects.aggregate(Max('server_knowledge'))['server_knowledge__max'] or 0

    result = YnabAdapter.get_uncleared_expenses(last_server_knowledge)

    if 'error' in result:
        raise Exception(result['error'])

    transactions = result['data']['transactions']
    new_server_knowledge = result['data']['server_knowledge']

    ynab_import = YnabImport(user=user, execution_datetime=datetime.now(), server_knowledge=new_server_knowledge)
    ynab_import.save()

    for t in transactions:
        YnabTransaction.objects.update_or_create(
            id=t['id'],
            defaults={
                "date": datetime.strptime(t['date'], "%Y-%m-%d").date(),
                "amount": t['amount'] / 1000,
                "memo": t['memo'],
                "cleared": t['cleared'],
                "approved": t['approved'],
                "flag_color": t['flag_color'],
                "flag_name": t['flag_name'],
                "account_id": t['account_id'],
                "payee_id": t['payee_id'],
                "category_id": t['category_id'],
                "transfer_account_id": t['transfer_account_id'],
                "transfer_transaction_id": t['transfer_transaction_id'],
                "matched_transaction_id": t['matched_transaction_id'],
                "import_id": t['import_id'],
                "debt_transaction_type": t['debt_transaction_type'],
                "deleted": t['deleted'],
                "user": user,
                "local_import": ynab_import,
            }
        )
