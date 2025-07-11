from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from core.mutations import sync_ynab_categories
from settings.base import YNAB_PERSONAL_BUDGET_ID, YNAB_SHARED_BUDGET_ID


@login_required
@require_POST
def synchronize_ynab_categories(request):
	"""
	Synchronize YNAB categories with local database
	"""
	sync_ynab_categories(YNAB_PERSONAL_BUDGET_ID)
	sync_ynab_categories(YNAB_SHARED_BUDGET_ID)
	return redirect('ynab-synchronizations-list')