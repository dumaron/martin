from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from core.models import BankTransaction


@login_required
@require_POST
def snooze_bank_transaction(request, bank_transaction_id):
	"""
	Snoozes a bank transaction. Useful for transactions that are actually just money transfers like reloading the debit card
	"""
	bank_transaction = get_object_or_404(BankTransaction, pk=bank_transaction_id)
	redirect_to = request.POST.get('redirect-to')
	bank_transaction.snoozed_on = datetime.now()
	bank_transaction.save()
	return redirect(redirect_to)

