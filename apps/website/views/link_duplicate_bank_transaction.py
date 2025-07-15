from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET

from core.models import BankTransaction


@login_required
@require_GET
def link_duplicate_bank_transaction(request, duplicate_transaction_id):
	"""
	Links a bank transaction as a duplicate of another transaction.
	The transaction ID from the URL becomes a duplicate of the transaction from the query parameter.
	"""
	# Get the original transaction ID from the query parameter
	original_transaction_id_str = request.GET.get('bank_transaction')
	
	# Validate that the bank_transaction parameter was provided
	if not original_transaction_id_str:
		return HttpResponseBadRequest('bank_transaction parameter is required')
	
	original_transaction_id = int(original_transaction_id_str)

	# Get both transactions
	duplicate_transaction = get_object_or_404(BankTransaction, pk=duplicate_transaction_id)
	original_transaction = get_object_or_404(BankTransaction, pk=original_transaction_id)

	# Prevent a transaction from being set as a duplicate of itself
	if duplicate_transaction_id == original_transaction_id:
		return HttpResponseBadRequest('A transaction cannot be set as a duplicate of itself')

	# Prevent a transaction that is already a duplicate from being set as a duplicate again
	if duplicate_transaction.duplicate_of is not None:
		return HttpResponseBadRequest('Transaction is already marked as a duplicate of another transaction')

	# Make the URL transaction a duplicate of the query parameter transaction
	duplicate_transaction.duplicate_of = original_transaction
	duplicate_transaction.save()

	# Redirect back to the original transaction detail page or wherever specified
	redirect_to = request.GET.get('redirect-to', f'/finances/bank_transactions/{original_transaction_id}')
	return redirect(redirect_to)
