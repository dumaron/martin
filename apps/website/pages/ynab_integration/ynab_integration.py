from django.shortcuts import redirect, render

from apps.website.pages.page import Page
from core.mutations import sync_ynab_categories, sync_ynab_transactions
from settings import YNAB_PERSONAL_BUDGET_ID, YNAB_SHARED_BUDGET_ID

page = Page(name='ynab_integration_page', base_route='integrations/ynab')


@page.main
def main_render(request):
	"""
	Shows a list of possible operations to sync local database with YNAB APIs
	"""
	return render(request, 'ynab_integration/ynab_synchronizations.html', {})


@page.action('synchronize-categories')
def synchronize_categories(request):
	"""
	Synchronize YNAB categories with local database
	"""
	sync_ynab_categories(YNAB_PERSONAL_BUDGET_ID)
	sync_ynab_categories(YNAB_SHARED_BUDGET_ID)
	return redirect('ynab_integration_page.main_render')


@page.action('sync')
def sync(request):
	"""
	Synchronizes local transactions with the ones in YNAB, taking the latter as a source of truth. Can work both in
	partial mode or "full" mode.
	"""
	partial_mode = request.POST['ynab-sync'] == 'partial-sync'

	# Each sync call synchronizes both personal and shared transactions
	sync_ynab_transactions(YNAB_SHARED_BUDGET_ID, partial_mode)
	sync_ynab_transactions(YNAB_PERSONAL_BUDGET_ID, partial_mode)

	return redirect('ynab_integration_page.main_render')
