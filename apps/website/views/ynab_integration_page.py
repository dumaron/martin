from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.mutations import sync_ynab_categories, sync_ynab_transactions
from settings import YNAB_PERSONAL_BUDGET_ID, YNAB_SHARED_BUDGET_ID


@login_required
@require_GET
def ynab_integration_page(request):
	"""
	Shows a list of possible operations to sync local database with YNAB APIs
	"""
	return render(request, 'ynab_synchronizations.html', {})


@login_required
@require_POST
def synchronize_ynab_categories(request):
	"""
	Synchronize YNAB categories with local database
	"""
	sync_ynab_categories(YNAB_PERSONAL_BUDGET_ID)
	sync_ynab_categories(YNAB_SHARED_BUDGET_ID)
	return redirect('ynab_integration_page')


@login_required
@require_POST
def ynab_sync(request):
	"""
	Synchronizes local transactions with the ones in YNAB, taking the latter as a source of truth. Can work both in
	partial mode or "full" mode.
	"""
	partial_mode = request.POST['ynab-sync'] == 'partial-sync'

	# Each sync call synchronizes both personal and shared transactions
	sync_ynab_transactions(YNAB_SHARED_BUDGET_ID, partial_mode)
	sync_ynab_transactions(YNAB_PERSONAL_BUDGET_ID, partial_mode)

	return redirect('ynab_integration_page')

