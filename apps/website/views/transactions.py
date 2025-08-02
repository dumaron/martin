import django_tables2 as tables
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.models import BankTransaction, YnabTransaction


class BankTransactionTable(tables.Table):
	id = tables.LinkColumn('bank_transaction_detail', args=[tables.A('pk')], verbose_name='ID')
	name = tables.Column(verbose_name='Description')
	date = tables.DateColumn(verbose_name='Date')
	amount = tables.Column(verbose_name='Amount')
	bank_account = tables.Column(verbose_name='Bank Account')

	class Meta:
		model = BankTransaction
		template_name = 'django_tables2/table.html'
		fields = ('id', 'name', 'date', 'amount', 'bank_account')


@login_required
@require_GET
def bank_transaction_detail(request, bank_transaction_id):
	bank_transaction = get_object_or_404(BankTransaction, pk=bank_transaction_id)
	similar_text = bank_transaction.get_similar_transactions(10)
	return render(
		request,
		'bank_transaction_detail.html',
		{'bank_transaction': bank_transaction, 'similar_text': similar_text},
	)


@login_required
@require_GET
def bank_transaction_list(request):
	table = BankTransactionTable(BankTransaction.objects.all().order_by('-date'))
	tables.RequestConfig(request).configure(table)
	return render(request, 'bank_transaction_list.html', {'table': table})


@login_required
@require_GET
def ynab_transaction_detail(request, ynab_transaction_id):
	ynab_transaction = get_object_or_404(YnabTransaction, pk=ynab_transaction_id)
	return render(request, 'ynab_transaction_detail.html', {'ynab_transaction': ynab_transaction})
