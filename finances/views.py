from django.shortcuts import render, redirect, get_object_or_404
from .models import BankExpense, YnabTransaction, YnabImport
from finances.adapters import ynab
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from .forms import BankImportForm
from finances.actions.sync_ynab_categories import sync_ynab_categories
from .actions.sync_ynab_transactions import sync_ynab_transactions


@login_required
@require_http_methods(['POST'])
def ynab_sync(request):
    """
    Synchronizes local transactions with the ones in YNAB, taking the latter as a source of truth. Can work both in
    partial mode or "full" mode.
    """
    if 'ynab-sync' in request.POST:
        partial_mode = request.POST['ynab-sync'] == 'partial-sync'
        sync_ynab_transactions(partial_mode, request.user)

    return redirect('pairing_v2')


def debug(request):
    print(request.POST)
    return render(request, 'partial.html')


@login_required
def expenses_pairing_view(request):
    unpaired_expenses = BankExpense.objects.filter(ynab_transaction_id=None, snoozed_on=None).order_by('-date')
    ynab_transactions = (
        YnabTransaction
        .objects
        .filter(cleared=YnabTransaction.ClearedStatuses.UNCLEARED, deleted=False)
        .order_by('-date'))
    return render(request, 'pairing.html', {
        'expenses': unpaired_expenses,
        'ynab_transactions': ynab_transactions,
    })


@login_required
def pairing_view_v2(request):
    first_unpaired_expense = BankExpense.objects.filter(snoozed_on=None, paired_on=None).order_by('-date').first()

    if first_unpaired_expense is None:
        return render(request, 'pairing_v2_empty.html', {})

    same_amount_suggestions = YnabTransaction.objects.filter(
        amount=first_unpaired_expense.amount, 
        cleared=YnabTransaction.ClearedStatuses.UNCLEARED) if first_unpaired_expense is not None else None

    similar_date_suggestions = YnabTransaction.objects.filter(
        date__lte=first_unpaired_expense.date + timedelta(days=3),
        date__gte=first_unpaired_expense.date - timedelta(days=3),
        cleared=YnabTransaction.ClearedStatuses.UNCLEARED) if first_unpaired_expense is not None else None
    

    return render(request, 'pairing_v2.html', {
        'expense': first_unpaired_expense,
        'same_amount_suggestions': same_amount_suggestions,
        'similar_date_suggestions': similar_date_suggestions,
    })


@login_required
@require_POST
def pair_expense_with_ynab_transaction(request):
    """
    Pair an expense with a YNAB transaction
    """
    transaction_id = request.POST['ynab-transaction']
    expense_id = request.POST['expense']

    transaction = get_object_or_404(YnabTransaction, pk=transaction_id)
    expense = get_object_or_404(BankExpense, pk=expense_id)

    # Sometimes I record transactions in YNAB with a slightly different amount of money. Given that the bank expense is
    # always the source of truth, I can decide to override the YNAB amount attribute when pairing to make them match
    # without having to do it manually through app or web interface
    amount = expense.amount if request.POST.get('override-amount', None) == 'true' else None

    result = ynab.clear_transaction(transaction, amount)

    if result['data']:
        transaction.cleared = YnabTransaction.ClearedStatuses.CLEARED
        if amount is not None:
            transaction.amount = amount
        transaction.save()
        expense.ynab_transaction_id = transaction_id
        expense.paired_on = datetime.now()
        expense.save()

    return redirect('pairing_v2')


@login_required
def file_import(request):
    if request.method == "POST":
        form = BankImportForm(request.POST, request.FILES)
        if form.is_valid():
            new_import = form.save(commit=False)
            new_import.user = request.user
            new_import.save()
            return redirect('pairing_v2')
        else:
            return render(request, 'file_import.html', {'form': form})
    else:
        form = BankImportForm()
        return render(request, 'file_import.html', {'form': form})
    

@login_required
@require_POST
def snooze_bankexpense(request, bankexpense_id):
    """
    Snoozes a bank expense. Useful for expenses that are actually just money transfers, like reloading the debit card
    """
    expense = get_object_or_404(BankExpense, pk=bankexpense_id)
    expense.snoozed_on = datetime.now()
    expense.save()
    return redirect('pairing_v2')


@login_required
@require_GET
def ynab_synchronizations_list(request):
    """
    Shows a list of possible operations to sync local database with YNAB APIs
    """
    return render(request, 'ynab_synchronizations.html', {})


@login_required
@require_POST
def synchronize_ynab_categories(request):
    """
    Synchronize YNAB categories with local database
    """
    sync_ynab_categories()
    return redirect('pairing_v2')