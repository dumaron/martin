import django_tables2 as tables
from django.shortcuts import render

from apps.website.pages.page import Page
from core.models import BankTransaction


class BankTransactionTable(tables.Table):
	id = tables.LinkColumn('bank_transaction_detail_page.main_render', args=[tables.A('pk')], verbose_name='ID')
	name = tables.Column(verbose_name='Description')
	date = tables.DateColumn(verbose_name='Date', format='Y-m-d')
	amount = tables.Column(verbose_name='Amount')
	bank_account = tables.Column(verbose_name='Bank Account')

	class Meta:
		model = BankTransaction
		template_name = 'django_tables2/table.html'
		fields = ('id', 'name', 'date', 'amount', 'bank_account')


page = Page(name='bank_transaction_list_page', base_route='models/bank-transaction')


@page.main
def main_render(request):
	table = BankTransactionTable(BankTransaction.objects.all().order_by('-date'))
	tables.RequestConfig(request).configure(table)
	return render(request, 'bank_transaction_list/bank_transaction_list.html', {'table': table})
