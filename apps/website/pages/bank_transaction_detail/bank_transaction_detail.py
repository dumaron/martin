from django.shortcuts import get_object_or_404, render

from apps.website.pages.page import Page
from core.models import BankTransaction

page = Page(
	name='bank_transaction_detail_page', base_route='models/bank-transaction/<int:bank_transaction_id>'
)


@page.main
def main_render(request, bank_transaction_id):
	bank_transaction = get_object_or_404(BankTransaction, pk=bank_transaction_id)
	return render(
		request, 'bank_transaction_detail/bank_transaction_detail.html', {'bank_transaction': bank_transaction}
	)
