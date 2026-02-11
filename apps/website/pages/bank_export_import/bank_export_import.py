from django import forms
from django.shortcuts import redirect, render

from apps.website.pages.page import Page
from core.models import BankFileImport


class BankFileImportForm(forms.ModelForm):
	class Meta:
		model = BankFileImport
		fields = ['bank_file', 'file_type']


page = Page(name='import_bank_export_page', base_route='pages/import-bank-export')


@page.main
def main_render(request):
	"""
	Page to allow importing bank exports from banks (Unicredit, Fineco, Credem)
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
