from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.website.forms import PersonalBankImportForm, YnabTransactionCreationForm
from core.actions import (
   create_ynab_transaction_from_bank_expense,
   pair_bank_expense_with_ynab_transaction,
   sync_ynab_categories,
   sync_ynab_transactions,
)
from core.models import BankExpense, YnabCategory, YnabTransaction
from settings.base import YNAB_PERSONAL_BUDGET_ID, YNAB_SHARED_BUDGET_ID


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
   partial_mode = request.POST['ynab-sync'] == 'partial-sync'

   # Each sync call synchronizes both personal and shared transactions
   sync_ynab_transactions(YNAB_SHARED_BUDGET_ID, partial_mode)
   sync_ynab_transactions(YNAB_PERSONAL_BUDGET_ID, partial_mode)

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

   same_amount_suggestions = (
      YnabTransaction.objects.filter(
         deleted=False, amount=first_unpaired_expense.amount, cleared=YnabTransaction.ClearedStatuses.UNCLEARED
      )
      if first_unpaired_expense is not None
      else None
   )

   similar_date_suggestions = (
      YnabTransaction.objects.filter(
         deleted=False,
         date__lte=first_unpaired_expense.date + timedelta(days=3),
         date__gte=first_unpaired_expense.date - timedelta(days=3),
         cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
      )
      if first_unpaired_expense is not None
      else None
   )

   return render(
      request,
      'pairing.html',
      {
         'expense': first_unpaired_expense,
         'same_amount_suggestions': same_amount_suggestions,
         'similar_date_suggestions': similar_date_suggestions,
         'ynab_categories': ynab_categories,
         'transaction_creation_form': YnabTransactionCreationForm(
            initial={'bank_expense_id': first_unpaired_expense.id}
         ),
      },
   )


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
def file_import_personal(request):
   """
   GET: Page to allow importing bank exports for personal banks (Unicredit, Fineco)
   POST: Form action to import personal bank export
   """
   if request.method == 'POST':
      form = PersonalBankImportForm(request.POST, request.FILES)
      if form.is_valid():
         form.save()
         return redirect('pairing')
      else:
         return render(request, 'file_import_personal.html', {'form': form})
   else:
      form = PersonalBankImportForm()
      return render(request, 'file_import_personal.html', {'form': form})


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
   sync_ynab_categories(YNAB_PERSONAL_BUDGET_ID)
   sync_ynab_categories(YNAB_SHARED_BUDGET_ID)
   return redirect('ynab-synchronizations-list')


@login_required
@require_POST
def create_ynab_transaction(request):
   """
   Creates a new YNAB transaction based on a bank expense and form data.

   Takes a POST request with form data containing:
   - bank_expense_id: ID of the BankExpense to create transaction from
   - memo: Optional memo text for the transaction
   - ynab_category: Category ID to assign to the transaction

   Returns redirect to pairing view on success, or None if form validation fails.
   """
   form = YnabTransactionCreationForm(request.POST)
   if form.is_valid():
      bank_expense = get_object_or_404(BankExpense, pk=form.cleaned_data['bank_expense_id'])
      memo = form.cleaned_data['memo']
      category_id = form.cleaned_data['ynab_category']
      create_ynab_transaction_from_bank_expense(bank_expense, memo, category_id)
      return redirect('pairing')
   else:
      return
