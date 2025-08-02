from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET


@login_required
@require_GET
def ynab_synchronizations_list(request):
	"""
	Shows a list of possible operations to sync local database with YNAB APIs
	"""
	return render(request, 'ynab_synchronizations.html', {})
