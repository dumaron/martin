import django_tables2 as tables
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.models import BankTransaction, BankFileImport, YnabTransaction


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


class BankFileImportTable(tables.Table):
	id = tables.LinkColumn('bank_file_import_detail', args=[tables.A('pk')], verbose_name='ID')
	bank_name = tables.Column(empty_values=(), verbose_name='Bank')
	import_date = tables.DateTimeColumn(verbose_name='Import Date')
	transaction_count = tables.Column(empty_values=(), verbose_name='Transactions Created')

	class Meta:
		model = BankFileImport
		template_name = 'django_tables2/table.html'
		fields = ('id', 'bank_name', 'import_date', 'transaction_count')

	def render_bank_name(self, record):
		file_type_to_bank = {
			'UNICREDIT_BANK_ACCOUNT_CSV_EXPORT': 'Unicredit',
			'UNICREDIT_DEBIT_CARD_CSV_EXPORT': 'Unicredit',
			'FINECO_BANK_ACCOUNT_XLSX_EXPORT': 'Fineco',
			'CREDEM_CSV_EXPORT': 'Credem',
		}
		return file_type_to_bank.get(record.file_type, record.file_type)



@login_required
@require_GET
def bank_transaction_detail(request, bank_transaction_id):
	bank_transaction = get_object_or_404(BankTransaction, pk=bank_transaction_id)
	return render(
		request,
		'bank_transaction_detail.html',
		{'bank_transaction': bank_transaction},
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


@login_required
@require_GET
def bank_file_import_detail(request, bank_file_import_id):
	bank_file_import = get_object_or_404(BankFileImport, pk=bank_file_import_id)
	bank_transactions = BankTransaction.objects.filter(file_import=bank_file_import).order_by('-date')
	bank_transactions_table = BankTransactionTable(bank_transactions)
	tables.RequestConfig(request, paginate=False).configure(bank_transactions_table)
	return render(
		request,
		'bank_file_import_detail.html',
		{
			'bank_file_import': bank_file_import,
			'bank_transactions_table': bank_transactions_table,
		},
	)


@login_required
@require_GET
def bank_file_import_list(request):
	table = BankFileImportTable(BankFileImport.objects.annotate(transaction_count=Count('banktransaction')).order_by('-import_date'))
	tables.RequestConfig(request).configure(table)
	return render(request, 'bank_file_import_list.html', {'table': table})
