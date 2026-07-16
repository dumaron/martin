from pathlib import Path

from django import forms
from django.shortcuts import redirect, render

from apps.website.pages.page import Page
from core.models import BankFileImport

FILE_TYPE_BY_EXTENSION = {
	'.xlsx': BankFileImport.FileType.FINECO_BANK_ACCOUNT_XLSX_EXPORT,
	'.csv': BankFileImport.FileType.CREDEM_CSV_EXPORT,
}


def detect_file_type(bank_file):
	return FILE_TYPE_BY_EXTENSION.get(Path(bank_file.name).suffix.lower())


class BankFileImportForm(forms.ModelForm):
	class Meta:
		model = BankFileImport
		fields = ['bank_file']

	def clean_bank_file(self):
		bank_file = self.cleaned_data['bank_file']

		if detect_file_type(bank_file) is None:
			raise forms.ValidationError('Unsupported file extension. Upload a Fineco .xlsx or a Credem .csv export.')

		return bank_file

	def save(self, commit=True):
		self.instance.file_type = detect_file_type(self.cleaned_data['bank_file'])
		return super().save(commit)


page = Page(name='import_bank_export_page', base_route='pages/import-bank-export')


@page.main
def main_render(request):
	"""
	Page to allow importing bank exports from banks (Fineco, Credem)
	"""
	form = BankFileImportForm()
	return render(request, 'bank_export_import/file_import.html', {'form': form})


@page.action('import')
def import_bank_export(request):
	"""
	Form action to import personal bank export
	"""
	form = BankFileImportForm(request.POST, request.FILES)

	if form.is_valid():
		bank_file_import = form.save()
		return redirect('bank_file_import_detail_page.main_render', bank_file_import_id=bank_file_import.id)
	else:
		return render(request, 'bank_export_import/file_import.html', {'form': form})
