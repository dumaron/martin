from datetime import datetime, timedelta

import django_tables2 as tables
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.website.forms import BankFileImportForm, YnabTransactionCreationForm
from core.functions import get_similar_bank_transactions
from core.models import BankTransaction, YnabTransaction
from core.mutations import (
	create_ynab_transaction_from_bank_expense,
	pair_bank_expense_with_ynab_transaction,
	sync_ynab_categories,
	sync_ynab_transactions,
)
from settings.base import YNAB_PERSONAL_BUDGET_ID, YNAB_SHARED_BUDGET_ID


class BankTransactionTable(tables.Table):
	id = tables.LinkColumn('bank_transaction_detail', args=[tables.A('pk')], verbose_name='ID')
	name = tables.Column(verbose_name='Description')
	date = tables.DateColumn(verbose_name='Date')
	amount = tables.Column(verbose_name='Amount')
	bank_account = tables.Column(verbose_name='Bank Account')

	class Meta:
		model = BankTransaction
		template_name = 'django_tables2/table.html'
		fields = ('id', 'name', 'date', 'amount', 'bank_account')


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

	return redirect('ynab-synchronizations-list')


@login_required
@require_GET
def pairing_view(request, kind):
	"""
	Second version of the pairing view. It is bank-expense centric: takes the oldest unpaired bank expense and shows
	some suggestions for pair-able YNAB transactions.
	"""

	personal = kind == 'personal'
	budget_id = YNAB_PERSONAL_BUDGET_ID if personal else YNAB_SHARED_BUDGET_ID

	first_unpaired_expense = (
		BankTransaction.objects
		.filter(snoozed_on=None, paired_on=None, bank_account__personal=personal)
		.order_by('date')
		.first()
	)

	if first_unpaired_expense is None:
		return render(request, 'pairing_empty.html', {})

	same_amount_suggestions = YnabTransaction.objects.filter(
		deleted=False,
		amount=first_unpaired_expense.amount,
		cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
		budget_id=budget_id,
	)

	similar_date_suggestions = YnabTransaction.objects.filter(
		deleted=False,
		date__lte=first_unpaired_expense.date + timedelta(days=3),
		date__gte=first_unpaired_expense.date - timedelta(days=3),
		cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
		budget_id=budget_id,
	)

	potential_duplicate = first_unpaired_expense.get_potential_duplicate()

	similar_bank_transactions = get_similar_bank_transactions(first_unpaired_expense.name, first_unpaired_expense.id, 5)

	return render(
		request,
		'pairing.html',
		{
			'kind': kind,
			'expense': first_unpaired_expense,
			'same_amount_suggestions': same_amount_suggestions,
			'similar_date_suggestions': similar_date_suggestions,
			'transaction_creation_form': YnabTransactionCreationForm(
				budget_id=budget_id, initial={'bank_expense_id': first_unpaired_expense.id}
			),
			'potential_duplicate': potential_duplicate if potential_duplicate else None,
			'similar_bank_transactions': similar_bank_transactions,
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
	redirect_to = request.POST.get('redirect-to')

	ynab_transaction = get_object_or_404(YnabTransaction, pk=transaction_id)
	bank_expense = get_object_or_404(BankTransaction, pk=expense_id)

	pair_bank_expense_with_ynab_transaction(bank_expense, ynab_transaction, override_amount)
	return redirect(redirect_to)


@login_required
def file_import(request):
	"""
	GET: Page to allow importing bank exports from banks (Unicredit, Fineco, Credem)
	POST: Form action to import personal bank export
	"""

	if request.method == 'POST':
		form = BankFileImportForm(request.POST, request.FILES)

		if form.is_valid():
			form.save()

			return redirect('file_import') # TODO create file import detail page
		else:
			return render(request, 'file_import.html', {'form': form })
	else:
		form = BankFileImportForm()
		return render(request, 'file_import.html', {'form': form })


@login_required
@require_POST
def snooze_bankexpense(request, bankexpense_id):
	"""
	Snoozes a bank expense. Useful for expenses that are actually just money transfers, like reloading the debit card
	"""
	expense = get_object_or_404(BankTransaction, pk=bankexpense_id)
	redirect_to = request.POST.get('redirect-to')
	expense.snoozed_on = datetime.now()
	expense.save()
	return redirect(redirect_to)


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
def create_ynab_transaction(request, kind):
	"""
	Creates a new YNAB transaction based on a bank expense and form data.

	Takes a POST request with form data containing:
	- bank_expense_id: ID of the BankExpense to create transaction from
	- memo: Optional memo text for the transaction
	- ynab_category: Category ID to assign to the transaction

	Returns redirect to pairing view on success, or None if form validation fails.
	"""

	personal = kind == 'personal'
	budget_id = YNAB_PERSONAL_BUDGET_ID if personal else YNAB_SHARED_BUDGET_ID
	form = YnabTransactionCreationForm(request.POST, budget_id=budget_id)
	redirect_to = request.POST.get('redirect-to')

	if form.is_valid():
		bank_expense = get_object_or_404(BankTransaction, pk=form.cleaned_data['bank_expense_id'])
		memo = form.cleaned_data['memo']
		category_id = form.cleaned_data['ynab_category']
		create_ynab_transaction_from_bank_expense(budget_id, bank_expense, memo, category_id)
		return redirect(redirect_to)
	else:
		return

@login_required
@require_GET
def bank_transaction_detail(request, bank_transaction_id):
	bank_transaction = get_object_or_404(BankTransaction, pk=bank_transaction_id)
	similar_text = get_similar_bank_transactions(bank_transaction.name, bank_transaction_id, 10)
	return render(request, 'bank_transation_detail.html', {
		'bank_transaction': bank_transaction,
		'similar_text': similar_text,
	})

@login_required
@require_GET
def bank_transaction_list(request):
	table = BankTransactionTable(BankTransaction.objects.all().order_by('-date'))
	tables.RequestConfig(request).configure(table)
	return render(request, 'bank_transaction_list.html', {'table': table})


@login_required
@require_GET
def ynab_transaction_detail(request, ynab_transaction_id):
	ynab_transaction = get_object_or_404(YnabTransaction, pk=ynab_transaction_id)
	return render(request, 'ynab_transaction_detail.html', { 'ynab_transaction': ynab_transaction })