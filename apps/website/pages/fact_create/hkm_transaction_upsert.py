import json
from operator import itemgetter

from django import forms
from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
from core import hkm
from core.hkm.models import Fact, Transaction
from core.utils.fp import lfilter, lmap, pipe, pluck


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


# The formset only generates independently stageable editor rows in the sidebar. The transaction form submits
# the JSON payload owned by each staged row instead of these controls.
FactFormSet = formset_factory(FactForm, extra=1)

# Its prefix and counter still give every dynamically added editor row distinct field names.
FORMSET_PREFIX = FactFormSet.get_default_prefix()
TOTAL_FORMS_FIELD = f'{FORMSET_PREFIX}-TOTAL_FORMS'
FACT_FIELDS = ('subject', 'predicate', 'object')


page = Page(name='fact_create_page', base_route='knowledge/transactions')


def _as_int(value, default=None):
	# For the ids and counters the browser sends: whatever it says, only a plain number is one. `isdecimal`
	# rather than `isdigit`, the latter also accepting things like '²', which then blow up in `int`.
	return int(value) if value.isdecimal() else default


def _retractable_by_id():
	# The offered facts, plus the same rows keyed by id — resolving an id back to the fact it names is what both
	# the picker and the save handler do with them.
	retractable = hkm.get_retractable_facts()
	return retractable, {fact['id']: fact for fact in retractable}


def _staged_fact(data):
	fact = {field: data[field] for field in FACT_FIELDS}
	fact['payload'] = json.dumps(fact, separators=(',', ':'))
	return fact


def _parse_staged_facts(payloads):
	facts = []
	invalid = False

	for payload in payloads:
		try:
			data = json.loads(payload)
		except (TypeError, json.JSONDecodeError):
			invalid = True
			continue

		if not isinstance(data, dict):
			invalid = True
			continue

		form = FactForm(data)
		if form.is_valid():
			facts.append(_staged_fact(form.cleaned_data))
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
			lambda fact: _staged_fact(
				{'subject': fact.subject, 'predicate': fact.predicate, 'object': fact.object}
			),
			transaction.facts.order_by('id'),
		)
		staged_retractions = transaction.retractions.values_list('fact_id', flat=True)

	formset = FactFormSet(form_kwargs={'empty_permitted': True})
	retractable, facts_by_id = _retractable_by_id()

	context = {
		'formset': formset,
		'staged_facts': staged_facts,
		# `description` is nullable (mutations store an empty note as NULL), and a None here would render as
		# the literal 'None' inside the textarea — so normalise to '' the way the save handler already does.
		'description': (transaction.description or '') if transaction else '',
		'form_error': None,
		'transaction': transaction,
		'entity_options': hkm.get_all_entities(),
		'predicate_options': hkm.get_used_predicates(),
		'retractable': retractable,
		# Staged ids come out of the database already parsed and unique. `lfilter` still has something to do:
		# a fact staged by this draft may have stopped being current since, and there is no row to show for it.
		'selected_retractions': pipe(staged_retractions, lmap(facts_by_id.get), lfilter(bool)),
		'draft_transactions': [] if transaction else hkm.get_draft_transactions(),
	}

	return render(request, 'fact_create/hkm_transaction_upsert.html', context)


@page.partial('fact-row')
def fact_row(request):
	"""
	One more fact editor row, appended to the sidebar by HTMX.

	The browser sends the current formset counter so every editor gets a distinct prefix. The response increments
	the counter out of band; final submission ignores these editor fields and reads the staged JSON payloads.
	"""
	index = _as_int(request.GET.get(TOTAL_FORMS_FIELD, ''), 0)
	context = {
		# A lone form standing in for the index-th editor, so its fields share one unique prefix.
		'form': FactForm(prefix=f'{FORMSET_PREFIX}-{index}', use_required_attribute=False, empty_permitted=True),
		'formset_prefix': FORMSET_PREFIX,
		'total_forms': index + 1,
	}
	return render(request, 'fact_create/partial_fact_row.html', context)


@page.partial('stage-fact')
def stage_fact(request):
	form = FactForm(request.GET, prefix=request.GET.get('prefix'))
	if not form.is_valid():
		return HttpResponse(status=422)

	return render(request, 'fact_create/stage_fact.html', {'fact': _staged_fact(form.cleaned_data)})


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
	return render(request, 'fact_create/retraction_facts_search.html', context)

@page.partial('stage-fact-retraction')
def stage_fact_retraction(request):
	fact_id = request.GET.get('fact_id')
	fact = get_object_or_404(Fact, pk=fact_id)
	return render(request, 'fact_create/stage_retraction.html', { 'fact': fact })


@page.action('<int?:transaction_id>/save')
def save_hkm_transaction(request, transaction_id=None):
	# Create and update in one handler: parse the submitted batch, stage it (as a new draft transaction or
	# replacing the one being edited) and land on the review page; on a problem, re-render the form as sent.
	transaction = None

	if transaction_id:
		transaction = get_object_or_404(Transaction, pk=transaction_id)
		if transaction.applied_at:
			return redirect('fact_review_page.main_render', transaction_id=transaction.id)

	formset = FactFormSet(form_kwargs={'empty_permitted': True})
	staged_facts, invalid_facts = _parse_staged_facts(request.POST.getlist('facts'))
	description = request.POST.get('description', '').strip()
	error = 'One or more staged facts are invalid.' if invalid_facts else None

	# The picker's hidden inputs are the whole story of what to retract. Resolving them against what is
	# retractable right now is what keeps a stale or forged id out of the batch, and the facts that survive are
	# also the rows to render back should this save fail. `dict.fromkeys` dedupes, keeping the order they came in.
	retractable, facts_by_id = _retractable_by_id()
	selected_retractions = pipe(
		request.POST.getlist('retractions'),
		lmap(_as_int),
		dict.fromkeys,
		lmap(facts_by_id.get),
		lfilter(bool),
	)
	retractions = list(pluck('id', selected_retractions))

	if not invalid_facts:
		facts = lmap(itemgetter(*FACT_FIELDS), staged_facts)
		if facts or retractions:
			if transaction is None:
				transaction = hkm.create_draft_transaction(facts, retractions=retractions, description=description)
			else:
				hkm.update_draft(transaction, facts, retractions=retractions, description=description)
			return redirect('fact_review_page.main_render', transaction_id=transaction.id)
		error = 'Add at least one fact or retraction before saving.'

	# `draft_transactions` stays empty here: main_render is the entry point for anything draft-related, so
	# parked transactions resurface there rather than on a form that failed to save.
	context = {
		'formset': formset,
		'staged_facts': staged_facts,
		'description': description,
		'form_error': error,
		'transaction': transaction,
		'entity_options': hkm.get_all_entities(),
		'predicate_options': hkm.get_used_predicates(),
		'retractable': retractable,
		'selected_retractions': selected_retractions,
		'draft_transactions': (),
	}

	return render(request, 'fact_create/hkm_transaction_upsert.html', context)
