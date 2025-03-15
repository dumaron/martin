from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from core.actions import create_ynab_transaction_from_bank_expense, pair_bank_expense_with_ynab_transaction, \
	sync_ynab_categories, sync_ynab_transactions
from core.models import BankExpense, YnabCategory, YnabTransaction
from apps.website.forms import BankImportForm, YnabTransactionCreationForm


@login_required
@require_GET
def martin_home_page(request):
	"""
	The Martin initial page. Tomorrow it'll contain pictures of the people I love, or inspiring quotes/images.
	Right now, I need to adapt.
	"""

	return render(request, 'home.html', {})


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

    return redirect('pairing')


@login_required
@require_GET
def pairing_view(request):
    """
    Second version of the pairing view. It is bank-expense centric: takes the oldest unpaired bank expense and shows
    some suggestions for pair-able YNAB transactions.
    """
    first_unpaired_expense = BankExpense.objects.filter(snoozed_on=None, paired_on=None).order_by('date').first()

    if first_unpaired_expense is None:
        return render(request, 'pairing_empty.html', {})

    ynab_categories = YnabCategory.objects.filter(hidden=False)

    same_amount_suggestions = YnabTransaction.objects.filter(
        deleted=False,
        amount=first_unpaired_expense.amount,
        cleared=YnabTransaction.ClearedStatuses.UNCLEARED) if first_unpaired_expense is not None else None

    similar_date_suggestions = YnabTransaction.objects.filter(
        deleted=False,
        date__lte=first_unpaired_expense.date + timedelta(days=3),
        date__gte=first_unpaired_expense.date - timedelta(days=3),
        cleared=YnabTransaction.ClearedStatuses.UNCLEARED) if first_unpaired_expense is not None else None

    return render(request, 'pairing.html', {
        'expense': first_unpaired_expense,
        'same_amount_suggestions': same_amount_suggestions,
        'similar_date_suggestions': similar_date_suggestions,
        'ynab_categories': ynab_categories,
        'transaction_creation_form': YnabTransactionCreationForm(initial={'bank_expense_id': first_unpaired_expense.id})
    })


@login_required
@require_POST
def pair_expense_with_ynab_transaction(request):
    """
    Pairs an expense with a YNAB transaction
    """
    transaction_id = request.POST['ynab-transaction']
    expense_id = request.POST['expense']
    override_amount = request.POST.get('override-amount', False) == 'true'

    ynab_transaction = get_object_or_404(YnabTransaction, pk=transaction_id)
    bank_expense = get_object_or_404(BankExpense, pk=expense_id)

    pair_bank_expense_with_ynab_transaction(bank_expense, ynab_transaction, override_amount)
    return redirect('pairing')


@login_required
def file_import(request):
    """
    Page to allow uploading files from banks export
    """
    if request.method == "POST":
        form = BankImportForm(request.POST, request.FILES)
        if form.is_valid():
            new_import = form.save(commit=False)
            new_import.user = request.user
            new_import.save()
            return redirect('pairing')
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
    return redirect('pairing')


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
    sync_ynab_categories(request.user)
    return redirect('ynab-synchronizations-list')


@login_required
@require_POST
def create_ynab_transaction(request):
    """
    TODO
    """
    form = YnabTransactionCreationForm(request.POST)
    if form.is_valid():
        bank_expense = get_object_or_404(BankExpense, pk=form.cleaned_data['bank_expense_id'])
        memo = form.cleaned_data['memo']
        category_id = form.cleaned_data['ynab_category']
        create_ynab_transaction_from_bank_expense(bank_expense, memo, category_id )
        return redirect('pairing')
    else:
        return
