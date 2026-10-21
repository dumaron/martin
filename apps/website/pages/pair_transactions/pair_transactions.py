import re
from datetime import datetime, timedelta
from decimal import Decimal

from django import forms, template
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django_htmx.http import HttpResponseClientRefresh

from apps.website.pages.page import Page
from apps.website.utils import highlight_text_differences
from core.models import BankTransaction, BankTransactionDescriptionHint, YnabCategory, YnabTransaction
from core.mutations import (
	create_ynab_transaction_from_bank_transaction,
	pair_bank_transaction_with_ynab_transaction,
)
from core.utils.fp import lmap
from settings.base import YNAB_PERSONAL_BUDGET_ID, YNAB_SHARED_BUDGET_ID


class YnabTransactionCreationForm(forms.Form):
	memo = forms.CharField()
	bank_transaction_id = forms.IntegerField(widget=forms.HiddenInput)
	ynab_category = forms.ModelChoiceField(
		queryset=YnabCategory.objects.none(), widget=forms.Select(attrs={'class': 'tom-select'})
	)

	def __init__(self, *args, budget_id, **kwargs):
		super().__init__(*args, **kwargs)

		# update the category field now that we have the budget_id available
		filtered_queryset = YnabCategory.objects.filter(budget_id=budget_id, hidden=False)
		self.fields['ynab_category'].queryset = filtered_queryset


PAIRED_SEARCH_LIMIT = 20
PAIRING_DATE_WINDOW = timedelta(days=15)

register = template.Library()


@register.filter(name='date_diff_level')
def get_date_diff_level(date_diff):
	distance = abs(date_diff)
	if distance == 0:
		return 'equal'
	if distance < 5:
		return 'green'
	if distance < 10:
		return 'yellow'
	return 'red'


def get_amount_tolerance(bank_amount):
	return max(Decimal(1), abs(bank_amount) * Decimal('0.1'))


@register.filter(name='amount_diff_level')
def get_amount_diff_level(amount_diff, bank_amount):
	distance = abs(amount_diff)
	if distance == 0:
		return 'equal'
	if distance < 1:
		return 'green'
	if distance < get_amount_tolerance(bank_amount):
		return 'yellow'
	return 'red'


def get_pairing_amount_window(amount):
	return min(1, abs(amount * Decimal('0.1')))


@register.filter(name='date_diff')
def get_pairing_date_distance(ynab_transaction, bank_transaction):
	return abs((bank_transaction.date - ynab_transaction.date).days)


@register.filter(name='amount_diff')
def get_pairing_amount_distance(ynab_transaction, bank_transaction):
	return abs(bank_transaction.amount - Decimal(str(ynab_transaction.amount)))


def sort_by_pairing_distance(bank_transaction, ynab_transactions):
	return sorted(
		ynab_transactions,
		key=lambda ynab_transaction: (
			get_pairing_date_distance(ynab_transaction, bank_transaction),
			get_pairing_amount_distance(ynab_transaction, bank_transaction),
		),
	)


def split_on_matches(text, query):
	if not query:
		return [(text, False)]

	return lmap(
		lambda indexed_part: (indexed_part[1], indexed_part[0] % 2 == 1),
		enumerate(re.split(f'({re.escape(query)})', text, flags=re.IGNORECASE)),
	)


page = Page(name='pair_transactions_page', base_route='flows/pair-transactions')


# TODO update description
@page.main('<str:kind>')
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
		return render(request, 'pair_transactions/pairing_empty.html', {})

	#
	amount_window = get_pairing_amount_window(first_unpaired_bank_transaction.amount)

	candidate_ynab_transactions = YnabTransaction.objects.filter(
		deleted=False,
		date__range=(
			first_unpaired_bank_transaction.date - PAIRING_DATE_WINDOW,
			first_unpaired_bank_transaction.date + PAIRING_DATE_WINDOW,
		),
		amount__range=(
			first_unpaired_bank_transaction.amount - amount_window,
			first_unpaired_bank_transaction.amount + amount_window,
		),
		cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
		budget_id=budget_id,
	)

	best_matches = sort_by_pairing_distance(first_unpaired_bank_transaction, candidate_ynab_transactions)

	potential_duplicate = first_unpaired_bank_transaction.get_potential_duplicate()
	potential_duplicate_highlighted = None

	if potential_duplicate:
		potential_duplicate_highlighted = highlight_text_differences(
			first_unpaired_bank_transaction.description, potential_duplicate.description
		)

	return render(
		request,
		'pair_transactions/pairing.html',
		{
			'kind': kind,
			'bank_transaction': first_unpaired_bank_transaction,
			'best_matches': best_matches,
			'transaction_creation_form': YnabTransactionCreationForm(
				budget_id=budget_id, initial={'bank_transaction_id': first_unpaired_bank_transaction.id}
			),
			'potential_duplicate': potential_duplicate,
			'potential_duplicate_highlighted': potential_duplicate_highlighted,
		},
	)


@page.partial('paired-transactions-search')
def paired_transactions_search(request):
	query = request.GET.get('paired-query', '').strip()
	return render(
		request,
		'pair_transactions/partial_paired_transactions_search.html',
		{
			'query': query,
			'results': lmap(
				lambda bank_transaction: {
					'bank_transaction': bank_transaction,
					'description_parts': split_on_matches(bank_transaction.description, query),
				},
				BankTransaction.search_paired_by_description(query)[:PAIRED_SEARCH_LIMIT],
			),
		},
	)


@page.action('save-description-hint')
def save_description_hint(request):
	text = request.POST.get('text', '').strip()
	hint = (request.htmx.prompt or '').strip()

	if not text or not hint:
		return HttpResponseBadRequest('Both the text and the hint are required')

	BankTransactionDescriptionHint.create_from_text(text, hint)
	return HttpResponseClientRefresh()


@page.action('pair-transactions')
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


@page.action('snooze-bank-transaction')
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


@page.action('link-duplicate-bank-transactions')
def link_duplicate_bank_transactions(request):
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
	default_redirect = reverse(
		'bank_transaction_detail_page.main_render', kwargs={'bank_transaction_id': target_bank_transaction_id}
	)
	redirect_to = request.POST.get('redirect-to', default_redirect)
	return redirect(redirect_to)


@page.action('create-ynab-transaction')
def create_ynab_transaction(request):
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
		return HttpResponseBadRequest('Invalid form data')
