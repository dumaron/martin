from django.shortcuts import render, redirect, get_object_or_404
from .models import BankExpense, YnabTransaction, YnabImport
from services.ynab import ynab
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(['POST'])
def ynab_sync(request):
    if 'ynab-sync' in request.POST:
        mode = request.POST['ynab-sync']
        date = None

        if mode == 'partial-sync':
            last_ynab_import = YnabImport.objects.latest('execution_datetime')
            if last_ynab_import is not None:
                date = last_ynab_import.execution_datetime - timedelta(days=30)
                date = date.date()

        ynab_expenses = ynab.get_uncleared_expenses(start_from=date)
        transactions = ynab_expenses['data']['transactions']
        ynab_import = YnabImport(user=request.user, execution_datetime=datetime.now())
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
                    "user": request.user,
                    "local_import": ynab_import,
                }
            )
        return redirect('expenses_pairing_view')


def debug(request):
    print(request.POST)
    return render(request, 'partial.html')


@login_required
def expenses_pairing_view(request):
    unpaired_expenses = BankExpense.objects.filter(ynab_transaction_id=None).order_by('-date')
    ynab_transactions = (
        YnabTransaction
        .objects
        .filter(cleared=YnabTransaction.ClearedStatuses.UNCLEARED)
        .order_by('-date'))
    return render(request, 'pairing.html', {
        'expenses': unpaired_expenses,
        'ynab_transactions': ynab_transactions,
    })


@login_required()
def pair_expense_with_ynab_transaction(request):
    transaction_id = request.POST['ynab-transaction']
    expense_id = request.POST['expense']
    transaction = get_object_or_404(YnabTransaction, pk=transaction_id)
    expense = get_object_or_404(BankExpense, pk=expense_id)
    result = ynab.clear_transaction(transaction)

    if result['data']:
        transaction.cleared = YnabTransaction.ClearedStatuses.CLEARED
        transaction.save()
        expense.ynab_transaction_id = transaction_id
        expense.save()

    return redirect('expenses_pairing_view')