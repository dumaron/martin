from django import forms

from core.models import BankFileImport, YnabCategory


class PersonalBankImportForm(forms.ModelForm):
	class Meta:
		model = BankFileImport
		fields = ['bank_file', 'file_type']


class SharedBankImportForm(forms.ModelForm):
	class Meta:
		model = BankFileImport
		fields = ['bank_file', 'file_type']
		widgets = {'file_type': forms.HiddenInput()}


class YnabTransactionCreationForm(forms.Form):
	memo = forms.CharField(widget=forms.Textarea)
	bank_expense_id = forms.IntegerField(widget=forms.HiddenInput)
	ynab_category = forms.ModelChoiceField(queryset=YnabCategory.objects.none())

	def __init__(self, *args, budget_id, **kwargs):
		super().__init__(*args, **kwargs)

		# update the category field now that we have the budget_id available
		filtered_queryset = YnabCategory.objects.filter(budget_id=budget_id, hidden=False)
		self.fields['ynab_category'].queryset = filtered_queryset
