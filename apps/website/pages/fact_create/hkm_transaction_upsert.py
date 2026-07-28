from operator import itemgetter

from django import forms
from django.forms import formset_factory
from django.http import HttpResponse
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
#
# Hence the `empty_permitted` every instantiation below passes its forms: a fully blanked row then validates to
# an empty cleaned_data, which the save handler skips. That is also how a prefilled row is removed when editing
# a draft transaction — clear it and save.
FactFormSet = formset_factory(FactForm, extra=1)

# The formset's own prefix ('form'), which names both the field counting the rows Django will bind and the
# prefix of each row ('form-3-subject'). The row partial needs both, so keep the string in one place.
FORMSET_PREFIX = FactFormSet.get_default_prefix()
TOTAL_FORMS_FIELD = f'{FORMSET_PREFIX}-TOTAL_FORMS'


page = Page(name='fact_create_page', base_route='knowledge/add')


def _as_int(value, default=None):
	# For the ids and counters the browser sends: whatever it says, only a plain number is one. `isdecimal`
	# rather than `isdigit`, the latter also accepting things like '²', which then blow up in `int`.
	return int(value) if value.isdecimal() else default


def _retractable_by_id():
	# The offered facts, plus the same rows keyed by id — resolving an id back to the fact it names is what both
	# the picker and the save handler do with them.
	retractable = hkm.get_retractable_facts()
	return retractable, {fact['id']: fact for fact in retractable}


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

	formset = FactFormSet(initial=staged_facts, form_kwargs={'empty_permitted': True})
	retractable, facts_by_id = _retractable_by_id()

	context = {
		'formset': formset,
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
	One more fact row, appended to the form by HTMX.

	The browser says how many rows it already has by sending the formset's TOTAL_FORMS along (see `hx-include`
	in the template), and the response carries that counter back, incremented, as an out-of-band swap — Django
	binds exactly the number of rows the management form declares, so an appended row that does not bump it
	would be ignored on save. That counter is the only thing setting this apart from a row the page renders
	itself, hence the same template for both.
	"""
	index = _as_int(request.GET.get(TOTAL_FORMS_FIELD, ''), 0)
	context = {
		# A lone form standing in for the index-th form of the formset, so it carries that form's prefix and
		# the POST binds it like any row rendered by the formset itself. `use_required_attribute=False` is what
		# `BaseFormSet._construct_form` passes its own forms: a row left blank here is legal, and the attribute
		# may not be combined with `empty_permitted` anyway.
		'form': FactForm(prefix=f'{FORMSET_PREFIX}-{index}', use_required_attribute=False, empty_permitted=True),
		'formset_prefix': FORMSET_PREFIX,
		'total_forms': index + 1,
	}
	return render(request, 'fact_create/partial_fact_row.html', context)


@page.partial('retraction-row')
def retraction_row(request):
	"""
	One selected-retraction row, appended to the picker by HTMX.

	`retraction_query` is the datalist value to resolve, `retractions` the rows the picker already holds (see
	`hx-include` in the template). A value naming no retractable fact, or naming one that is already in, has no
	row to answer with: 204 tells HTMX to leave the page alone, which is also what keeps a search committed
	twice — the field both changing and the button being clicked — from adding the fact twice.

	Which fact is retractable no longer depends on the draft being edited, so unlike the page around it this
	partial needs nothing of the transaction.
	"""
	_, facts_by_id = _retractable_by_id()
	# The datalist offers "<id>: <subject> — <predicate> — <object>", a label alone not being unique, so the id
	# is whatever sits before the first colon.
	queried_id = _as_int(request.GET.get('retraction_query', '').strip().split(':', 1)[0])
	held = set(lmap(_as_int, request.GET.getlist('retractions')))

	if queried_id not in facts_by_id or queried_id in held:
		return HttpResponse(status=204)

	return render(request, 'fact_create/partial_retraction_row.html', {'fact': facts_by_id[queried_id]})


@page.action('<int?:transaction_id>/save')
def save_hkm_transaction(request, transaction_id=None):
	# Create and update in one handler: parse the submitted batch, stage it (as a new draft transaction or
	# replacing the one being edited) and land on the review page; on a problem, re-render the form as sent.
	transaction = None

	if transaction_id:
		transaction = get_object_or_404(Transaction, pk=transaction_id)
		if transaction.applied_at:
			return redirect('fact_review_page.main_render', transaction_id=transaction.id)

	formset = FactFormSet(request.POST, form_kwargs={'empty_permitted': True})
	description = request.POST.get('description', '').strip()
	error = None

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
