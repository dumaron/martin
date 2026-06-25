from django import forms
from django.forms import BaseFormSet, formset_factory
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


class BaseFactFormSet(BaseFormSet):
	def clean(self):
		if any(self.errors):
			return
		if not any(self.cleaned_data):
			raise forms.ValidationError('Add at least one fact before saving.')


FactFormSet = formset_factory(FactForm, formset=BaseFactFormSet, extra=1)


page = Page(name='fact_create_page', base_route='knowledge/add')


def _form_kwargs():
	return {'entities': list(hkm.get_all_entities()), 'predicates': list(hkm.get_used_predicates())}


@page.main
def main_render(request):
	formset = FactFormSet(form_kwargs=_form_kwargs())
	return render(request, 'fact_create/fact_create.html', {'formset': formset})


@page.action('save')
def create_facts(request):
	formset = FactFormSet(request.POST, form_kwargs=_form_kwargs())
	description = request.POST.get('description', '').strip()
	if formset.is_valid():
		facts = [(d['subject'], d['predicate'], d['object']) for d in formset.cleaned_data if d]
		draft = hkm.create_draft(facts, description=description)
		return redirect('fact_review_page.main_render', transaction_id=draft.id)
	return render(request, 'fact_create/fact_create.html', {'formset': formset, 'description': description})
