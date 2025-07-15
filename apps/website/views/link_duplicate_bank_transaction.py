from django.contrib.auth.decorators import login_required
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
	original_transaction_id = request.GET['bank_transaction']

	# Get both transactions
	duplicate_transaction = get_object_or_404(BankTransaction, pk=duplicate_transaction_id)
	original_transaction = get_object_or_404(BankTransaction, pk=original_transaction_id)

	# Make the URL transaction a duplicate of the query parameter transaction
	duplicate_transaction.duplicate_of = original_transaction
	duplicate_transaction.save()

	# Redirect back to the original transaction detail page or wherever specified
	redirect_to = request.GET.get('redirect-to', f'/finances/bank_transactions/{original_transaction_id}')
	return redirect(redirect_to)
