from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.website.forms import YnabTransactionCreationForm
from core.models import BankTransaction
from core.mutations import create_ynab_transaction_from_bank_expense
from settings.base import YNAB_PERSONAL_BUDGET_ID, YNAB_SHARED_BUDGET_ID


@login_required
@require_POST
def create_ynab_transaction(request, kind):
	"""
	Creates a new YNAB transaction based on a bank expense and form data.

	Takes a POST request with form data containing:
	- bank_expense_id: ID of the BankExpense to create transaction from
	- memo: Optional memo text for the transaction
	- ynab_category: Category ID to assign to the transaction

	Returns redirect to pairing view on success, or None if form validation fails.
	"""

	personal = kind == 'personal'
	budget_id = YNAB_PERSONAL_BUDGET_ID if personal else YNAB_SHARED_BUDGET_ID
	form = YnabTransactionCreationForm(request.POST, budget_id=budget_id)
	redirect_to = request.POST.get('redirect-to')

	if form.is_valid():
		bank_expense = get_object_or_404(BankTransaction, pk=form.cleaned_data['bank_expense_id'])
		memo = form.cleaned_data['memo']
		category_id = form.cleaned_data['ynab_category']
		create_ynab_transaction_from_bank_expense(budget_id, bank_expense, memo, category_id)
		return redirect(redirect_to)
	else:
		return