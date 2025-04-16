from django import forms
from core.models import BankFileImport, YnabCategory


class PersonalBankImportForm(forms.ModelForm):
    class Meta:
        model = BankFileImport
        fields = ["bank_file", "file_type"]


class YnabTransactionCreationForm(forms.Form):
    memo = forms.CharField(widget=forms.Textarea)
    bank_expense_id = forms.IntegerField(widget=forms.HiddenInput)
    ynab_category = forms.ModelChoiceField(queryset=YnabCategory.objects.filter(hidden=False))
