from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from core.models import BankTransaction


@login_required
@require_POST
def snooze_bankexpense(request, bankexpense_id):
	"""
	Snoozes a bank expense. Useful for expenses that are actually just money transfers, like reloading the debit card
	"""
	expense = get_object_or_404(BankTransaction, pk=bankexpense_id)
	redirect_to = request.POST.get('redirect-to')
	expense.snoozed_on = datetime.now()
	expense.save()
	return redirect(redirect_to)
