from django.shortcuts import get_object_or_404, render

from apps.website.pages.page import Page
from core.models import YnabTransaction

page = Page(
	name='ynab_transaction_detail_page', base_route='models/ynab-transaction/<str:ynab_transaction_id>'
)


@page.main
def main_render(request, ynab_transaction_id):
	ynab_transaction = get_object_or_404(YnabTransaction, pk=ynab_transaction_id)
	return render(
		request, 'ynab_transaction_detail/ynab_transaction_detail.html', {'ynab_transaction': ynab_transaction}
	)
