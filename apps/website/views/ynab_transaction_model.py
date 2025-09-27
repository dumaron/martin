from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.models import YnabTransaction


@login_required
@require_GET
def ynab_transaction_detail(request, ynab_transaction_id):
	ynab_transaction = get_object_or_404(YnabTransaction, pk=ynab_transaction_id)
	return render(request, 'ynab_transaction_detail.html', {'ynab_transaction': ynab_transaction})
