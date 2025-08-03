from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.website.forms import BankFileImportForm


@login_required
def file_import(request):
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
