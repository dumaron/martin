from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.models import BankFileImport


class BankFileImportForm(forms.ModelForm):
	class Meta:
		model = BankFileImport
		fields = ['bank_file', 'file_type']


@login_required
@require_GET
def main_render(request):
	"""
	Page to allow importing bank exports from banks (Unicredit, Fineco, Credem)
	"""
	form = BankFileImportForm()
	return render(request, 'file_import.html', {'form': form})


@login_required
@require_POST
def import_bank_export(request):
	"""
	Form action to import personal bank export
	"""
	form = BankFileImportForm(request.POST, request.FILES)

	if form.is_valid():
		bank_file_import = form.save()
		return redirect('bank_file_import_detail_page.main_render', bank_file_import_id=bank_file_import.id)
	else:
		return render(request, 'file_import.html', {'form': form})
