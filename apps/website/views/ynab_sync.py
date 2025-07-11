from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from core.mutations import sync_ynab_transactions
from settings.base import YNAB_PERSONAL_BUDGET_ID, YNAB_SHARED_BUDGET_ID


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

	return redirect('ynab-synchronizations-list')