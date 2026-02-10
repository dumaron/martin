import django_tables2 as tables
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

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


@login_required
@require_GET
def main_render(request):
	table = BankTransactionTable(BankTransaction.objects.all().order_by('-date'))
	tables.RequestConfig(request).configure(table)
	return render(request, 'bank_transaction_list_page/bank_transaction_list.html', {'table': table})
