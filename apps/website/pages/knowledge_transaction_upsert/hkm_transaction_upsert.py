import json
from operator import itemgetter

from django import forms
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
from core import hkm
from core.hkm.models import CurrentFact, Fact, Transaction
from core.utils.fp import lmap


class FactForm(forms.Form):
	# Each field is a CharField rendered as a plain text input backed by a datalist: the browser offers known
	# values while still accepting a brand-new string.
	subject = forms.CharField(
		widget=forms.TextInput(
			attrs={
				'list': 'hkm-entity-options',
				'placeholder': 'subject (entity)',
			}
		)
	)
	predicate = forms.CharField(
		widget=forms.TextInput(
			attrs={
				'list': 'hkm-predicate-options',
				'placeholder': 'predicate',
			}
		)
	)
	object = forms.CharField(
		widget=forms.TextInput(
			attrs={
				'list': 'hkm-entity-options',
				'placeholder': 'object (entity or value)',
			}
		)
	)


FACT_FIELDS = ('subject', 'predicate', 'object')


page = Page(name='knowledge_transaction_upsert_page', base_route='knowledge/transactions')


def _as_int(value, default=None):
	# For ids the browser sends: whatever it says, only a plain number is one. `isdecimal` rather than
	# `isdigit`, the latter also accepting things like '²', which then blow up in `int`.
	return int(value) if value.isdecimal() else default


# TODO TODO rework this
def serialize_staged_fact(data):
	fact = {field: data[field] for field in FACT_FIELDS}
	fact['payload'] = json.dumps([fact[field] for field in FACT_FIELDS], separators=(',', ':'))
	return fact


def parse_serialized_facts(payloads):
	facts = []
	invalid = False

	for payload in payloads:
		try:
			data = json.loads(payload)
		except (TypeError, json.JSONDecodeError):
			invalid = True
			continue

		if not isinstance(data, list) or len(data) != len(FACT_FIELDS):
			invalid = True
			continue

		form = FactForm(dict(zip(FACT_FIELDS, data)))
		if form.is_valid():
			facts.append(serialize_staged_fact(form.cleaned_data))
		else:
			invalid = True

	return facts, invalid


# A first interesting case where my "page" abstraction looks a bit stretched: both transaction creation and update
# share the same template, form, and some logic. So, to avoid having to create a "shared" folder, I made this page
# available at two URLs.
# Not super-happy, but I think I can also change my perspective and see this as a single page with just an optional
# argument, a draft transaction ID. Mah.
@page.main('new')
@page.main('<int:transaction_id>/edit')
def main_render(request, transaction_id=None):
	transaction = None
	staged_facts = []
	staged_retractions = []

	if transaction_id:
		transaction = get_object_or_404(Transaction, pk=transaction_id)

		if transaction.applied_at:
			return redirect('fact_review_page.main_render', transaction_id=transaction.id)

		# Existing facts are already staged operations, while the sidebar starts with a fresh editor row.
		staged_facts = lmap(
			lambda fact: serialize_staged_fact(
				{'subject': fact.subject, 'predicate': fact.predicate, 'object': fact.object}
			),
			transaction.facts.order_by('id'),
		)
		staged_retractions = [
			retraction.fact
			for retraction in transaction.retractions.select_related('fact').order_by('fact_id')
		]

	context = {
		'form': FactForm(),
		'staged_facts': staged_facts,
		'description': (transaction.description or '') if transaction else '',
		'transaction': transaction,
		'entity_options': hkm.get_all_entities(),
		'predicate_options': hkm.get_used_predicates(),
		'staged_retractions': staged_retractions,
		'draft_transactions': [] if transaction else hkm.get_draft_transactions(),
	}

	return render(request, 'knowledge_transaction_upsert/hkm_transaction_upsert.html', context)



@page.partial('stage-fact')
def stage_fact(request):
	form = FactForm(request.GET)
	if not form.is_valid():
		return HttpResponse(status=422)

	return render(request, 'knowledge_transaction_upsert/stage_fact.html', {'fact': serialize_staged_fact(form.cleaned_data)})


@page.partial('retraction-facts-search')
def retraction_facts_search(request):
	search_query = request.GET.get('retraction-query')
	staged_retraction_ids = {
		fact_id
		for value in request.GET.getlist('retractions')
		if (fact_id := _as_int(value)) is not None
	}
	context = {
		'search_query': search_query,
		'facts': [
			fact
			for fact in hkm.search_retractable_facts(search_query)
			if fact['id'] not in staged_retraction_ids
		],
	}
	return render(request, 'knowledge_transaction_upsert/retraction_facts_search.html', context)

@page.partial('stage-fact-retraction')
def stage_fact_retraction(request):
	fact_id = request.GET.get('fact_id')
	fact = get_object_or_404(Fact, pk=fact_id)
	return render(request, 'knowledge_transaction_upsert/stage_retraction.html', {'fact': fact})


@page.action('<int?:transaction_id>/save')
def save_hkm_transaction(request, transaction_id=None):
	# Create and update in one handler: parse the submitted batch, stage it (as a new draft transaction or
	# replacing the one being edited) and land on the review page; on a problem, re-render the form as sent.
	transaction = None

	if transaction_id:
		transaction = get_object_or_404(Transaction, pk=transaction_id)
		if transaction.applied_at:
			return redirect('fact_review_page.main_render', transaction_id=transaction.id)

	staged_facts, invalid_facts = parse_serialized_facts(request.POST.getlist('facts'))
	description = request.POST.get('description', '').strip()
	error = 'One or more staged facts are invalid.' if invalid_facts else None

	# Only current facts may be retracted. Resolve the submitted IDs directly against that view instead of
	# loading every retractable fact; the set also deduplicates repeated hidden inputs.
	staged_retraction_ids = {
		fact_id
		for value in request.POST.getlist('retractions')
		if (fact_id := _as_int(value)) is not None
	}
	staged_retractions = list(
		CurrentFact.objects.filter(id__in=staged_retraction_ids).order_by('subject', 'predicate', 'object')
	)
	retracted_fact_ids = [fact.id for fact in staged_retractions]

	if not invalid_facts:
		facts = lmap(itemgetter(*FACT_FIELDS), staged_facts)
		if facts or retracted_fact_ids:
			if transaction is None:
				transaction = hkm.create_draft_transaction(facts, retractions=retracted_fact_ids, description=description)
			else:
				hkm.update_draft(transaction, facts, retractions=retracted_fact_ids, description=description)
			return redirect('fact_review_page.main_render', transaction_id=transaction.id)
		error = 'Add at least one fact or retraction before saving.'

	# `draft_transactions` stays empty here: main_render is the entry point for anything draft-related, so
	# parked transactions resurface there rather than on a form that failed to save.
	context = {
		'form': FactForm(),
		'staged_facts': staged_facts,
		'description': description,
		'form_error': error,
		'transaction': transaction,
		'entity_options': hkm.get_all_entities(),
		'predicate_options': hkm.get_used_predicates(),
		'staged_retractions': staged_retractions,
		'draft_transactions': (),
	}

	return render(request, 'knowledge_transaction_upsert/hkm_transaction_upsert.html', context)
