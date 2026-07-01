from django import forms
from django.forms import formset_factory
from django.shortcuts import redirect, render

from apps.website.pages.page import Page
from core import hkm


class FactForm(forms.Form):
	# Each field is a CharField rendered as a <select> (not a ChoiceField): the dropdown offers known values
	# while Tom Select still lets you type a brand-new one. A ChoiceField would reject anything outside its
	# `choices`; a CharField accepts whatever string is submitted, which is exactly the "pick or create"
	# behaviour we want.
	subject = forms.CharField(
		widget=forms.Select(attrs={'class': 'hkm-select', 'data-placeholder': 'subject (entity)'})
	)
	predicate = forms.CharField(
		widget=forms.Select(attrs={'class': 'hkm-select', 'data-placeholder': 'predicate'})
	)
	object = forms.CharField(
		widget=forms.Select(attrs={'class': 'hkm-select', 'data-placeholder': 'object (entity or value)'})
	)

	def __init__(self, *args, entities=(), predicates=(), **kwargs):
		super().__init__(*args, **kwargs)
		self._populate('subject', entities)
		self._populate('predicate', predicates)
		self._populate('object', entities)

	def _populate(self, name, options):
		# Seed the <option>s with the known values, plus whatever was submitted, so a freshly typed value
		# stays selected if the form is re-rendered after a validation error.
		field = self.fields[name]
		values = list(options)
		submitted = self.data.get(self.add_prefix(name)) if self.is_bound else None
		if submitted and submitted not in values:
			values = [submitted, *values]
		field.widget.choices = [('', '')] + [(value, value) for value in values]


# A batch is valid with any mix of asserted facts and retractions, so the formset no longer requires a fact
# (the "at least one of either" check lives in the view). Per-form validation still rejects a half-filled row.
FactFormSet = formset_factory(FactForm, extra=1)


page = Page(name='fact_create_page', base_route='knowledge/add')


def _form_kwargs():
	return {'entities': list(hkm.get_all_entities()), 'predicates': list(hkm.get_used_predicates())}


def _context(formset, retractable, description='', form_error=None):
	return {'formset': formset, 'retractable': retractable, 'description': description, 'form_error': form_error}


@page.main
def main_render(request):
	formset = FactFormSet(form_kwargs=_form_kwargs())
	return render(request, 'fact_create/fact_create.html', _context(formset, hkm.get_retractable_facts()))


@page.action('save')
def create_facts(request):
	formset = FactFormSet(request.POST, form_kwargs=_form_kwargs())
	description = request.POST.get('description', '').strip()
	retractable = hkm.get_retractable_facts()
	if formset.is_valid():
		facts = [(d['subject'], d['predicate'], d['object']) for d in formset.cleaned_data if d]
		# Keep only ids that are genuinely retractable right now (guards against stale/forged selections).
		retractable_ids = {fact['id'] for fact in retractable}
		retractions = [
			int(value)
			for value in request.POST.getlist('retractions')
			if value.isdigit() and int(value) in retractable_ids
		]
		if facts or retractions:
			draft = hkm.create_draft(facts, retractions=retractions, description=description)
			return redirect('fact_review_page.main_render', transaction_id=draft.id)
		error = 'Add at least one fact or retraction before saving.'
		return render(request, 'fact_create/fact_create.html', _context(formset, retractable, description, error))
	return render(request, 'fact_create/fact_create.html', _context(formset, retractable, description))
