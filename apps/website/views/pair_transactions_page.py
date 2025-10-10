from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.website.forms import YnabTransactionCreationForm
from apps.website.utils import highlight_text_differences
from core.models import BankTransaction, YnabTransaction
from core.mutations import (
	create_ynab_transaction_from_bank_transaction,
	pair_bank_transaction_with_ynab_transaction,
)
from settings.base import YNAB_PERSONAL_BUDGET_ID, YNAB_SHARED_BUDGET_ID


# TODO update description
@require_GET
def pair_transactions_page(request, kind):
	"""
	Second version of the pairing view. It is bank transaction centric: takes the oldest unpaired bank transaction and shows
	some suggestions for pair-able YNAB transactions.
	"""

	personal = kind == 'personal'
	budget_id = YNAB_PERSONAL_BUDGET_ID if personal else YNAB_SHARED_BUDGET_ID

	first_unpaired_bank_transaction = (
		BankTransaction.objects.filter(
			snoozed_on=None, paired_on=None, duplicate_of=None, bank_account__personal=personal
		)
		# ↓ sort by ID technically not needed, but AI convinced me it's useful to avoid undeterministic behaviors during tests
		.order_by('date', 'id')
		.first()
	)

	if first_unpaired_bank_transaction is None:
		return render(request, 'pairing_empty.html', {})

	same_amount_suggestions = YnabTransaction.objects.filter(
		deleted=False,
		amount=first_unpaired_bank_transaction.amount,
		cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
		budget_id=budget_id,
	)

	similar_date_suggestions = YnabTransaction.objects.filter(
		deleted=False,
		date__lte=first_unpaired_bank_transaction.date + timedelta(days=3),
		date__gte=first_unpaired_bank_transaction.date - timedelta(days=3),
		cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
		budget_id=budget_id,
	)

	potential_duplicate = first_unpaired_bank_transaction.get_potential_duplicate()
	potential_duplicate_highlighted = None

	if potential_duplicate:
		potential_duplicate_highlighted = highlight_text_differences(
			first_unpaired_bank_transaction.name, potential_duplicate.name
		)

	return render(
		request,
		'pairing.html',
		{
			'kind': kind,
			'bank_transaction': first_unpaired_bank_transaction,
			'same_amount_suggestions': same_amount_suggestions,
			'similar_date_suggestions': similar_date_suggestions,
			'transaction_creation_form': YnabTransactionCreationForm(
				budget_id=budget_id, initial={'bank_transaction_id': first_unpaired_bank_transaction.id}
			),
			'potential_duplicate': potential_duplicate,
			'potential_duplicate_highlighted': potential_duplicate_highlighted,
		},
	)


@login_required
@require_POST
def pair_transactions(request):
	"""
	Pairs a bank transaction with a YNAB transaction
	"""
	transaction_id = request.POST.get('ynab-transaction')
	bank_transaction_id = request.POST.get('bank_transaction')
	override_amount = request.POST.get('override-amount', False) == 'true'
	redirect_to = request.POST.get('redirect-to')

	ynab_transaction = get_object_or_404(YnabTransaction, pk=transaction_id)
	bank_transaction = get_object_or_404(BankTransaction, pk=bank_transaction_id)

	pair_bank_transaction_with_ynab_transaction(bank_transaction, ynab_transaction, override_amount)
	return redirect(redirect_to)


@login_required
@require_POST
def snooze_bank_transaction(request):
	"""
	Snoozes a bank transaction. Useful for transactions that are actually just money transfers like reloading the debit card
	"""
	bank_transaction_id = int(request.POST.get('bank_transaction'))
	bank_transaction = get_object_or_404(BankTransaction, pk=bank_transaction_id)
	redirect_to = request.POST.get('redirect-to')
	bank_transaction.snoozed_on = datetime.now()
	bank_transaction.save()
	return redirect(redirect_to)


@login_required
@require_POST
def link_duplicate_bank_transaction(request):
	"""
	Links a bank transaction as a duplicate of another transaction.
	The transaction ID from the URL becomes a duplicate of the transaction from the query parameter.
	"""

	duplicate_transaction_id = int(request.POST.get('bank_transaction_id'))
	target_bank_transaction_id = int(request.POST.get('target_bank_transaction_id'))

	# Get both transactions
	duplicate_transaction = get_object_or_404(BankTransaction, pk=duplicate_transaction_id)
	target_transaction = get_object_or_404(BankTransaction, pk=target_bank_transaction_id)

	# TODO make the rest of the function a class method maybe?

	# Prevent a transaction from being set as a duplicate of itself
	if duplicate_transaction_id == target_bank_transaction_id:
		return HttpResponseBadRequest('A transaction cannot be set as a duplicate of itself')

	# Prevent a transaction that is already a duplicate from being set as a duplicate again
	if target_transaction.duplicate_of is not None:
		return HttpResponseBadRequest('Transaction is already marked as a duplicate of another transaction')

	# Make the URL transaction a duplicate of the query parameter transaction
	# THOUGHT: Should this be a BankTransaction method? And maybe all the validation too should be there?
	target_transaction.duplicate_of = duplicate_transaction
	target_transaction.save()

	# Redirect back to the original transaction detail page or wherever specified
	redirect_to = request.POST.get('redirect-to', f'/finances/bank_transactions/{target_bank_transaction_id}')
	return redirect(redirect_to)


@login_required
@require_POST
def create_ynab_transaction(request, kind):
	"""
	Creates a new YNAB transaction based on a bank transaction and form data.

	Takes a POST request with form data containing:
	- bank_transaction_id: ID of the BankTransaction to create transaction from
	- memo: Optional memo text for the transaction
	- ynab_category: Category ID to assign to the transaction

	Returns redirect to pairing view on success, or None if form validation fails.
	"""

	personal = request.POST.get('kind') == 'personal'
	budget_id = YNAB_PERSONAL_BUDGET_ID if personal else YNAB_SHARED_BUDGET_ID
	form = YnabTransactionCreationForm(request.POST, budget_id=budget_id)
	redirect_to = request.POST.get('redirect-to')

	if form.is_valid():
		bank_transaction = get_object_or_404(BankTransaction, pk=form.cleaned_data['bank_transaction_id'])
		memo = form.cleaned_data['memo']
		category_id = form.cleaned_data['ynab_category']
		create_ynab_transaction_from_bank_transaction(budget_id, bank_transaction, memo, category_id)
		return redirect(redirect_to)
	else:
		return # TODO fix this, maybe returning an HTTP code?
