from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.models import BankTransaction


@login_required
@require_GET
def main_render(request, bank_transaction_id):
	bank_transaction = get_object_or_404(BankTransaction, pk=bank_transaction_id)
	return render(request, 'bank_transaction_detail.html', {'bank_transaction': bank_transaction})
