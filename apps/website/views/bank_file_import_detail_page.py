import django_tables2 as tables
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.models import BankFileImport, BankTransaction


class BankTransactionTable(tables.Table):
	id = tables.LinkColumn('bank_transaction_detail_page.main_render', args=[tables.A('pk')], verbose_name='ID')
	name = tables.Column(verbose_name='Description')
	date = tables.DateColumn(verbose_name='Date', format='Y-m-d')
	amount = tables.Column(verbose_name='Amount')
	duplicate_of = tables.LinkColumn(
		verbose_name='Duplicate of?',
		accessor='duplicate_of',
		default='',
		viewname='bank_transaction_detail_page.main_render',
		args=[tables.A('duplicate_of.pk')],
		text=lambda record: f'BT-{record.duplicate_of.pk}' if record.duplicate_of else '',
	)

	class Meta:
		model = BankTransaction
		template_name = 'django_tables2/table.html'
		fields = ('id', 'name', 'date', 'amount', 'duplicate_of')


@login_required
@require_GET
def main_render(request, bank_file_import_id):
	bank_file_import = get_object_or_404(BankFileImport, pk=bank_file_import_id)
	bank_transactions = BankTransaction.objects.filter(file_import=bank_file_import).order_by('-date')

	time_window_days = 0
	first_transaction = bank_transactions.first()
	last_transaction = bank_transactions.last()
	if first_transaction and last_transaction:
		time_window_days = (first_transaction.date - last_transaction.date).days

	bank_transactions_table = BankTransactionTable(bank_transactions)
	tables.RequestConfig(request, paginate=False).configure(bank_transactions_table)
	return render(
		request,
		'bank_file_import_detail.html',
		{
			'bank_file_import': bank_file_import,
			'bank_transactions_table': bank_transactions_table,
			'first_transaction': first_transaction,
			'last_transaction': last_transaction,
			'time_window_days': time_window_days,
		},
	)
