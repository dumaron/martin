from operator import itemgetter

from django import forms
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
from core import hkm
from core.hkm.models import Transaction
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


# A batch is valid with any mix of asserted facts and retractions, so the formset no longer requires a fact
# (the "at least one of either" check lives in the view). Per-form validation still rejects a half-filled row.
FactFormSet = formset_factory(FactForm, extra=1)


page = Page(name='fact_create_page', base_route='knowledge/add')


def _form_kwargs():
	# `empty_permitted` lets a fully blanked row validate to an empty cleaned_data (which the save handlers
	# skip). That is also how a prefilled row is removed when editing a draft transaction: clear it and save.
	return {'empty_permitted': True}


def _suggestion_values():
	return {
		'entity_options': list(hkm.get_all_entities()),
		'predicate_options': list(hkm.get_used_predicates()),
	}


# A first interesting case where my "page" abstraction looks a bit stretched: both transaction creation and update
# share the same template, form, and some logic. So, to avoid having to create a "shared" folder, I made this page
# available at two URLs.
# Not super-happy, but I think I can also change my perspective and see this as a single page with just an optional
# argument, a draft transaction ID. Mah.
@page.main('<int?:transaction_id>')
def main_render(request, transaction_id=None):
	transaction = None
	staged_facts = []
	staged_retractions = []

	if transaction_id:
		transaction = get_object_or_404(Transaction, pk=transaction_id)

		if transaction.applied_at:
			return redirect('fact_review_page.main_render', transaction_id=transaction.id)

		# The formset wants a list of dicts here, so this one stays a lambda: `itemgetter` works on the
		# mappings coming back out of `cleaned_data`, not on the Fact instances going in.
		staged_facts = lmap(
			lambda fact: {'subject': fact.subject, 'predicate': fact.predicate, 'object': fact.object},
			transaction.facts.order_by('id'),
		)
		staged_retractions = transaction.retractions.values_list('fact_id', flat=True)

	formset = FactFormSet(initial=staged_facts, form_kwargs=_form_kwargs())
	entity_options = hkm.get_all_entities()
	predicate_options = hkm.get_used_predicates()

	context = {
		'formset': formset,
		# `ignore_transaction_id` is what keeps this transaction's own staged retractions in the offered set —
		# without it they read as "already taken" and the rows they point at vanish from the picker.
		'retractable': hkm.get_retractable_facts(ignore_transaction_id=transaction.id if transaction else None),
		# `description` is nullable (mutations store an empty note as NULL), and a None here would render as
		# the literal 'None' inside the textarea — so normalise to '' the way the save handler already does.
		'description': (transaction.description or '') if transaction else '',
		'form_error': None,
		'transaction': transaction,
		'selected_retractions': staged_retractions,
		'entity_options': entity_options,
		'predicate_options': predicate_options,
		'draft_transactions': [] if transaction else hkm.get_draft_transactions(),
	}

	return render(request, 'fact_create/hkm_transaction_upsert.html', context)


@page.action('<int?:transaction_id>/save')
def save_hkm_transaction(request, transaction_id=None):
	# Create and update in one handler: parse the submitted batch, stage it (as a new draft transaction or
	# replacing the one being edited) and land on the review page; on a problem, re-render the form as sent.
	transaction = None

	if transaction_id:
		transaction = get_object_or_404(Transaction, pk=transaction_id)
		if transaction.applied_at:
			return redirect('fact_review_page.main_render', transaction_id=transaction.id)

	formset = FactFormSet(request.POST, form_kwargs=_form_kwargs())
	description = request.POST.get('description', '').strip()
	retractable = hkm.get_retractable_facts(ignore_transaction_id=transaction.id if transaction else None)
	error = None

	# Keep only ids that are genuinely retractable right now (guards against stale/forged selections).
	# `isdecimal` rather than `isdigit`: the latter also accepts things like '²', which then blow up in `int`.
	retractable_ids = set(pluck('id', retractable))
	retractions = pipe(
		request.POST.getlist('retractions'),
		lfilter(str.isdecimal),
		lmap(int),
		lfilter(lambda fact_id: fact_id in retractable_ids),
	)

	if formset.is_valid():
		# Blank rows validate to an empty cleaned_data (see `empty_permitted` above) — keep only the real ones.
		facts = pipe(
			formset.cleaned_data,
			lfilter(bool),
			lmap(itemgetter('subject', 'predicate', 'object')),
		)
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
		'retractable': retractable,
		'description': description,
		'form_error': error,
		'transaction': transaction,
		'selected_retractions': set(retractions),
		**_suggestion_values(),
		'draft_transactions': (),
	}

	return render(request, 'fact_create/hkm_transaction_upsert.html', context)
