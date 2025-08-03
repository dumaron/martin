from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from core.models import BankTransaction, YnabTransaction
from core.mutations import pair_bank_expense_with_ynab_transaction


@login_required
@require_POST
def match_transactions(request):
	"""
	Pairs a bank transaction with a YNAB transaction
	"""
	transaction_id = request.POST.get('ynab-transaction')
	expense_id = request.POST.get('expense')
	override_amount = request.POST.get('override-amount', False) == 'true'
	redirect_to = request.POST.get('redirect-to')

	ynab_transaction = get_object_or_404(YnabTransaction, pk=transaction_id)
	bank_transaction = get_object_or_404(BankTransaction, pk=expense_id)

	pair_bank_expense_with_ynab_transaction(bank_transaction, ynab_transaction, override_amount)
	return redirect(redirect_to)
