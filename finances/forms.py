from django import forms
from .models import BankFileImport, YnabCategory


class BankImportForm(forms.ModelForm):
    class Meta:
        model = BankFileImport
        fields = ["bank_file", "file_type"]


class YnabTransactionCreationForm(forms.Form):
    memo = forms.CharField(widget=forms.Textarea)
    bank_expense_id = forms.IntegerField(widget=forms.HiddenInput)
    shared_with_my_sweety = forms.BooleanField(required=False)
    ynab_category = forms.ModelChoiceField(queryset=YnabCategory.objects.filter(hidden=False))
