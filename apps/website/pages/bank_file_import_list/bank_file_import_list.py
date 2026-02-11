import django_tables2 as tables
from django.db.models import Count
from django.shortcuts import render

from apps.website.pages.page import Page
from core.models import BankFileImport


class BankFileImportTable(tables.Table):
	id = tables.LinkColumn('bank_file_import_detail_page.main_render', args=[tables.A('pk')], verbose_name='ID')
	bank_name = tables.Column(empty_values=(), verbose_name='Bank', accessor='bank')
	import_date = tables.DateTimeColumn(verbose_name='Import Date', format='Y-m-d H:i')
	transaction_count = tables.Column(empty_values=(), verbose_name='Transactions Created')

	class Meta:
		model = BankFileImport
		template_name = 'django_tables2/table.html'
		fields = ('id', 'bank_name', 'import_date', 'transaction_count')


page = Page(name='bank_file_import_list_page', base_route='models/bank-file-import')


@page.main
def main_render(request):
	table = BankFileImportTable(
		BankFileImport.objects.annotate(transaction_count=Count('banktransaction')).order_by('-import_date')
	)
	tables.RequestConfig(request).configure(table)
	return render(request, 'bank_file_import_list/bank_file_import_list.html', {'table': table})
