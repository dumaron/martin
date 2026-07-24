from django import forms
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
from core import hkm
from core.hkm.models import Transaction
from core.utils.fp import lfilter, lmap


class FactForm(forms.Form):
	# Each field is a CharField rendered as a plain text input backed by a datalist: the browser offers known
	# values while still accepting a brand-new string. A ChoiceField would reject anything outside its choices.
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


# A batch is valid with any mix of asserted facts and retractions, so the formset no longer requires a fact
# (the "at least one of either" check lives in the view). Per-form validation still rejects a half-filled row.
FactFormSet = formset_factory(FactForm, extra=1)


page = Page(name='fact_create_page', base_route='knowledge/add')


def _form_kwargs():
	# `empty_permitted` lets a fully blanked row validate to an empty cleaned_data (which the save handlers
	# skip). That is also how a prefilled row is removed when editing a draft: clear it out and save.
	return {'empty_permitted': True}


def _suggestion_values():
	return {
		'entity_options': list(hkm.get_all_entities()),
		'predicate_options': list(hkm.get_used_predicates()),
	}


def _context(
	formset,
	retractable,
	description='',
	form_error=None,
	draft=None,
	selected_retractions=(),
	entity_options=(),
	predicate_options=(),
):
	# `draft` is None on the create page and the draft being edited on the edit page; the template switches
	# the heading, the form action and the cancel link on it. `pending_drafts` is filled by main_render only:
	# the create page is the entry point for anything draft-related, so parked drafts resurface there.
	return {
		'formset': formset,
		'retractable': retractable,
		'description': description,
		'form_error': form_error,
		'draft': draft,
		'selected_retractions': selected_retractions,
		'entity_options': entity_options,
		'predicate_options': predicate_options,
		'pending_drafts': (),
	}


def _submitted_facts(formset):
	# Blank rows validate to an empty cleaned_data (see `empty_permitted` above) — keep only the real ones.
	rows = lfilter(None, formset.cleaned_data)
	return lmap(lambda row: (row['subject'], row['predicate'], row['object']), rows)


def _submitted_retractions(request, retractable):
	# Keep only ids that are genuinely retractable right now (guards against stale/forged selections).
	retractable_ids = {fact['id'] for fact in retractable}
	submitted = lmap(int, lfilter(str.isdigit, request.POST.getlist('retractions')))
	return lfilter(lambda fact_id: fact_id in retractable_ids, submitted)


def _handle_save(request, draft=None):
	# Shared by create and update: parse the submitted batch, stage it (as a new draft or replacing the one
	# being edited) and land on the review page; on any problem, re-render the form as submitted.
	formset = FactFormSet(request.POST, form_kwargs=_form_kwargs())
	suggestions = _suggestion_values()
	description = request.POST.get('description', '').strip()
	retractable = hkm.get_retractable_facts(ignore_transaction_id=draft.id if draft else None)
	retractions = _submitted_retractions(request, retractable)
	error = None
	if formset.is_valid():
		facts = _submitted_facts(formset)
		if facts or retractions:
			if draft is None:
				draft = hkm.create_draft_transaction(facts, retractions=retractions, description=description)
			else:
				hkm.update_draft(draft, facts, retractions=retractions, description=description)
			return redirect('fact_review_page.main_render', transaction_id=draft.id)
		error = 'Add at least one fact or retraction before saving.'
	context = _context(formset, retractable, description, error, draft, set(retractions), **suggestions)
	return render(request, 'fact_create/fact_create.html', context)


@page.main
def main_render(request):
	suggestions = _suggestion_values()
	formset = FactFormSet(form_kwargs=_form_kwargs())
	context = _context(formset, hkm.get_retractable_facts(), **suggestions)
	context['pending_drafts'] = hkm.get_draft_transactions()
	return render(request, 'fact_create/fact_create.html', context)


@page.action('save')
def create_facts(request):
	return _handle_save(request)


@page.action('<int:transaction_id>', method='GET')
def edit_draft(request, transaction_id):
	# The create page, prefilled with a draft's staged facts and retractions. Only drafts are editable:
	# applied transactions are immutable history, so we bounce to the review page, which explains that.
	draft = get_object_or_404(Transaction, pk=transaction_id)
	if draft.applied_at:
		return redirect('fact_review_page.main_render', transaction_id=draft.id)
	staged = lmap(
		lambda fact: {'subject': fact.subject, 'predicate': fact.predicate, 'object': fact.object},
		draft.facts.order_by('id'),
	)
	suggestions = _suggestion_values()
	formset = FactFormSet(initial=staged, form_kwargs=_form_kwargs())
	retractable = hkm.get_retractable_facts(ignore_transaction_id=draft.id)
	selected = set(draft.retractions.values_list('fact_id', flat=True))
	context = _context(
		formset,
		retractable,
		draft.description or '',
		draft=draft,
		selected_retractions=selected,
		**suggestions,
	)
	return render(request, 'fact_create/fact_create.html', context)


@page.action('<int:transaction_id>/save')
def update_facts(request, transaction_id):
	draft = get_object_or_404(Transaction, pk=transaction_id)
	if draft.applied_at:
		return redirect('fact_review_page.main_render', transaction_id=draft.id)
	return _handle_save(request, draft=draft)
