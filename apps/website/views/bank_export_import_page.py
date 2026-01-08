from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.models import BankFileImport


class BankFileImportForm(forms.ModelForm):
	class Meta:
		model = BankFileImport
		fields = ['bank_file', 'file_type']


@login_required
def import_bank_export_page(request):
	# TODO split this into GET and POST
	"""
	GET: Page to allow importing bank exports from banks (Unicredit, Fineco, Credem)
	POST: Form action to import personal bank export
	"""

	if request.method == 'POST':
		form = BankFileImportForm(request.POST, request.FILES)

		if form.is_valid():
			bank_file_import = form.save()

			return redirect('bank_file_import_detail', bank_file_import_id=bank_file_import.id)
		else:
			return render(request, 'file_import.html', {'form': form})
	else:
		form = BankFileImportForm()
		return render(request, 'file_import.html', {'form': form})
