from django.forms import ModelForm
from .models import BankFileImport


class BankImportForm(ModelForm):
    class Meta:
        model = BankFileImport
        fields = ["bank_file", "file_type"]
