import json
from dataclasses import dataclass
from typing import Self

from django import forms
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
from core import hkm
from core.hkm.models import CurrentFact, Fact, Transaction
from core.utils.fp import lmap


# I don't really like OOP... and here we are defining a class. But to be honest I think this has been necessary not
# because it is helping me as an abstraction here, but because of the friction this ecosystem presents when trying yo
# use a more functional and simple approach.
# Validation in magic __post_init__ method? Why can't I use something similar to zod to check the same things whenever
# I want in the variable lifecycle?
# And, look at all the useless code spent converting from tutple, or from dictionary, to this.
# I wanted to use `serialize_fact` as a function? Nope, otherwise you need to pass it to the template, unlike in JSX
# where you can simply call a function in it that is defined in the page.
#
# I don't know man... that feels bad when compared to Typescript.
@dataclass(frozen=True)
class StagedFact:
	subject: str
	predicate: str
	object: str

	def __post_init__(self) -> None:
		values = (self.subject, self.predicate, self.object)
		if not all(isinstance(value, str) for value in values):
			raise ValueError('Fact values must be strings')

		values = tuple(value.strip() for value in values)
		if not all(values):
			raise ValueError('Fact values cannot be empty')

		object.__setattr__(self, 'subject', values[0])
		object.__setattr__(self, 'predicate', values[1])
		object.__setattr__(self, 'object', values[2])

	@classmethod
	def from_fact(cls, fact: Fact) -> Self:
		return cls(fact.subject, fact.predicate, fact.object)

	@classmethod
	def from_data(cls, data: object) -> Self:
		if not isinstance(data, list) or len(data) != 3:
			raise ValueError('A staged fact must contain exactly three values')

		return cls(*data)

	@classmethod
	def from_serialized(cls, payload: str) -> Self:
		try:
			data = json.loads(payload)
		except (TypeError, json.JSONDecodeError) as error:
			raise ValueError('Invalid staged fact JSON') from error

		return cls.from_data(data)

	def as_tuple(self) -> tuple[str, str, str]:
		return self.subject, self.predicate, self.object

	def serialized(self) -> str:
		return json.dumps(self.as_tuple(), separators=(',', ':'))


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


page = Page(name='knowledge_transaction_upsert_page', base_route='knowledge/transactions')


# A first interesting case where my "page" abstraction looks a bit stretched: both transaction creation and update
# share the same template, form, and some logic. So, to avoid having to create a "shared" folder, I made this page
# available at two URLs.
# Not super-happy, but I think I can also change my perspective and see this as a single page with just an optional
# argument, a draft transaction ID. Mah.
@page.main(['new', '<int:transaction_id>/edit'])
def main_render(request: HttpRequest, transaction_id: int | None = None) -> HttpResponse:
	transaction: Transaction | None = None
	staged_facts: list[StagedFact] = []
	staged_retractions: list[Fact] = []

	if transaction_id is not None:
		transaction = get_object_or_404(Transaction, pk=transaction_id)

		if transaction.applied_at:
			return redirect('fact_review_page.main_render', transaction_id=transaction.id)

		# Existing facts are already staged operations, while the sidebar starts with a fresh editor row.
		staged_facts = [StagedFact.from_fact(fact) for fact in transaction.facts.order_by('id')]
		staged_retractions = [
			retraction.fact for retraction in transaction.retractions.select_related('fact').order_by('fact_id')
		]

	context = {
		'form': FactForm(),
		'description': (transaction.description or '') if transaction else '',
		'transaction': transaction,
		'entity_options': hkm.get_all_entities(),
		'predicate_options': hkm.get_used_predicates(),
		'staged_facts': staged_facts,
		'staged_retractions': staged_retractions,
		'draft_transactions': [] if transaction else hkm.get_draft_transactions(),
	}

	return render(request, 'knowledge_transaction_upsert/hkm_transaction_upsert.html', context)


@page.partial('stage-fact')
def stage_fact(request: HttpRequest) -> HttpResponse:
	form = FactForm(request.GET)
	if not form.is_valid():
		return HttpResponse(status=422)

	return render(
		request,
		'knowledge_transaction_upsert/stage_fact.html',
		{'staged_fact': StagedFact(**form.cleaned_data)},
	)


@page.partial('retraction-facts-search')
def retraction_facts_search(request: HttpRequest) -> HttpResponse:
	search_query = request.GET.get('retraction-query')
	staged_retraction_ids = set(request.GET.getlist('retractions'))
	context = {
		'search_query': search_query,
		'facts': [
			fact for fact in hkm.search_retractable_facts(search_query) if str(fact['id']) not in staged_retraction_ids
		],
	}
	return render(request, 'knowledge_transaction_upsert/retraction_facts_search.html', context)


@page.partial('stage-fact-retraction')
def stage_fact_retraction(request: HttpRequest) -> HttpResponse:
	fact_id = request.GET.get('fact_id')
	fact = get_object_or_404(Fact, pk=fact_id)
	return render(request, 'knowledge_transaction_upsert/stage_retraction.html', {'fact': fact})


@page.action('<int?:transaction_id>/save')
def save_hkm_transaction(request: HttpRequest, transaction_id: int | None = None) -> HttpResponse:
	# Create and update in one handler: parse the submitted batch, stage it (as a new draft transaction or
	# replacing the one being edited) and land on the review page; on a problem, re-render the form as sent.
	transaction: Transaction | None = None

	if transaction_id is not None:
		transaction = get_object_or_404(Transaction, pk=transaction_id)
		if transaction.applied_at:
			return redirect('fact_review_page.main_render', transaction_id=transaction.id)

	staged_facts: list[StagedFact] = []
	invalid_facts = False
	for payload in request.POST.getlist('facts'):
		try:
			staged_facts.append(StagedFact.from_serialized(payload))
		except ValueError:
			invalid_facts = True

	# Only current facts may be retracted. Resolve the submitted IDs directly against that view instead of
	# loading every retractable fact; the set also deduplicates repeated hidden inputs.
	staged_retraction_ids: set[int] = set()
	invalid_retractions = False
	for value in request.POST.getlist('retractions'):
		try:
			staged_retraction_ids.add(int(value))
		except ValueError:
			invalid_retractions = True

	staged_retractions = list(
		CurrentFact.objects.filter(id__in=staged_retraction_ids).order_by('subject', 'predicate', 'object')
	)
	retracted_fact_ids = [fact.id for fact in staged_retractions]

	description = request.POST.get('description', '').strip()
	if invalid_facts:
		error = 'One or more staged facts are invalid.'
	elif invalid_retractions:
		error = 'One or more staged retractions are invalid.'
	else:
		error = None

	if not invalid_facts and not invalid_retractions:
		facts = lmap(StagedFact.as_tuple, staged_facts)
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
