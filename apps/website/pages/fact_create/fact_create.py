from django import forms
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
from core import hkm
from core.hkm.models import Transaction
from core.utils.fp import lfilter, lmap


class FactForm(forms.Form):
	# Each field is a CharField rendered as a <select> (not a ChoiceField): the dropdown offers known values
	# while Tom Select still lets you type a brand-new one. A ChoiceField would reject anything outside its
	# `choices`; a CharField accepts whatever string is submitted, which is exactly the "pick or create"
	# behaviour we want.
	# `tom-select` + data-create* opt into the global "pick or create" initializer (see base.html).
	subject = forms.CharField(
		widget=forms.Select(
			attrs={
				'class': 'tom-select',
				'data-create': 'true',
				'data-create-on-blur': 'true',
				'data-placeholder': 'subject (entity)',
			}
		)
	)
	predicate = forms.CharField(
		widget=forms.Select(
			attrs={
				'class': 'tom-select',
				'data-create': 'true',
				'data-create-on-blur': 'true',
				'data-placeholder': 'predicate',
			}
		)
	)
	object = forms.CharField(
		widget=forms.Select(
			attrs={
				'class': 'tom-select',
				'data-create': 'true',
				'data-create-on-blur': 'true',
				'data-placeholder': 'object (entity or value)',
			}
		)
	)

	def __init__(self, *args, entities=(), predicates=(), **kwargs):
		super().__init__(*args, **kwargs)
		self._populate('subject', entities)
		self._populate('predicate', predicates)
		self._populate('object', entities)

	def _populate(self, name, options):
		# Seed the <option>s with the known values, plus the field's current value: what was submitted (so a
		# freshly typed value stays selected if the form is re-rendered after a validation error) or, for an
		# unbound form, its initial value (a staged fact being edited may hold a value — e.g. a typo — that is
		# not among the known entities/predicates, and it must still render as selected).
		field = self.fields[name]
		values = list(options)
		current = self.data.get(self.add_prefix(name)) if self.is_bound else self.initial.get(name)
		if current and current not in values:
			values = [current, *values]
		field.widget.choices = [('', '')] + [(value, value) for value in values]


# A batch is valid with any mix of asserted facts and retractions, so the formset no longer requires a fact
# (the "at least one of either" check lives in the view). Per-form validation still rejects a half-filled row.
FactFormSet = formset_factory(FactForm, extra=1)


page = Page(name='fact_create_page', base_route='knowledge/add')


def _form_kwargs():
	# `empty_permitted` lets a fully blanked row validate to an empty cleaned_data (which the save handlers
	# skip). That is also how a prefilled row is removed when editing a draft: clear it out and save.
	return {
		'entities': list(hkm.get_all_entities()),
		'predicates': list(hkm.get_used_predicates()),
		'empty_permitted': True,
	}


def _context(formset, retractable, description='', form_error=None, draft=None, selected_retractions=()):
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
	context = _context(formset, retractable, description, error, draft, set(retractions))
	return render(request, 'fact_create/fact_create.html', context)


@page.main
def main_render(request):
	formset = FactFormSet(form_kwargs=_form_kwargs())
	context = _context(formset, hkm.get_retractable_facts())
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
	formset = FactFormSet(initial=staged, form_kwargs=_form_kwargs())
	retractable = hkm.get_retractable_facts(ignore_transaction_id=draft.id)
	selected = set(draft.retractions.values_list('fact_id', flat=True))
	context = _context(formset, retractable, draft.description or '', draft=draft, selected_retractions=selected)
	return render(request, 'fact_create/fact_create.html', context)


@page.action('<int:transaction_id>/save')
def update_facts(request, transaction_id):
	draft = get_object_or_404(Transaction, pk=transaction_id)
	if draft.applied_at:
		return redirect('fact_review_page.main_render', transaction_id=draft.id)
	return _handle_save(request, draft=draft)
