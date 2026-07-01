from django import forms
from django.shortcuts import redirect, render

from apps.website.pages.page import Page
from core import hkm
from core.hkm.models import PredicateRule


class PredicateRuleForm(forms.ModelForm):
	class Meta:
		model = PredicateRule
		fields = ['source_predicate', 'implied_predicate', 'flip']
		widgets = {
			'source_predicate': forms.Select(attrs={'class': 'hkm-select', 'data-placeholder': 'source predicate'}),
			'implied_predicate': forms.Select(attrs={'class': 'hkm-select', 'data-placeholder': 'implied predicate'}),
		}

	def __init__(self, *args, predicates=(), **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['flip'].label = 'Reverse the edge'
		self.fields['flip'].help_text = (
			'Swap subject and object in the implied fact — for inverse (father-of → child-of) and symmetric '
			'(married-to → married-to) rules. Leave unchecked for a same-direction sub-property '
			'(father-of → parent-of).'
		)
		# CharField + Select (not ChoiceField) so an existing predicate can be picked or a new one typed, same
		# as the fact form. Seed the options from predicates already in use, plus any submitted value.
		for name in ('source_predicate', 'implied_predicate'):
			field = self.fields[name]
			values = list(predicates)
			submitted = self.data.get(name) if self.is_bound else None
			if submitted and submitted not in values:
				values = [submitted, *values]
			field.widget.choices = [('', '')] + [(value, value) for value in values]


page = Page(name='predicate_rule_page', base_route='knowledge/rules')


def _render(request, form):
	rules = PredicateRule.objects.order_by('source_predicate', 'implied_predicate', 'flip')
	return render(request, 'predicate_rule/predicate_rule.html', {'form': form, 'rules': rules})


@page.main
def main_render(request):
	return _render(request, PredicateRuleForm(predicates=list(hkm.get_used_predicates())))


@page.action('create')
def create_rule(request):
	form = PredicateRuleForm(request.POST, predicates=list(hkm.get_used_predicates()))
	if form.is_valid():
		form.save()
		return redirect('predicate_rule_page.main_render')
	return _render(request, form)


@page.action('<int:rule_id>/delete')
def delete_rule(request, rule_id):
	PredicateRule.objects.filter(id=rule_id).delete()
	return redirect('predicate_rule_page.main_render')
