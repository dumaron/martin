from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.website.forms import YnabTransactionCreationForm
from core.functions import get_similar_bank_transactions
from core.models import BankTransaction, YnabTransaction
from settings.base import YNAB_PERSONAL_BUDGET_ID, YNAB_SHARED_BUDGET_ID


@login_required
@require_GET
def pairing_view(request, kind):
	"""
	Second version of the pairing view. It is bank-expense centric: takes the oldest unpaired bank expense and shows
	some suggestions for pair-able YNAB transactions.
	"""

	personal = kind == 'personal'
	budget_id = YNAB_PERSONAL_BUDGET_ID if personal else YNAB_SHARED_BUDGET_ID

	first_unpaired_expense = (
		BankTransaction.objects
		.filter(snoozed_on=None, paired_on=None, bank_account__personal=personal)
		.order_by('date', 'id')  # <- sort by ID technically not needed, but AI convinced me it's useful to avoid undeterministic behaviors during tests
		.first()
	)

	if first_unpaired_expense is None:
		return render(request, 'pairing_empty.html', {})

	same_amount_suggestions = YnabTransaction.objects.filter(
		deleted=False,
		amount=first_unpaired_expense.amount,
		cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
		budget_id=budget_id,
	)

	similar_date_suggestions = YnabTransaction.objects.filter(
		deleted=False,
		date__lte=first_unpaired_expense.date + timedelta(days=3),
		date__gte=first_unpaired_expense.date - timedelta(days=3),
		cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
		budget_id=budget_id,
	)

	potential_duplicate = first_unpaired_expense.get_potential_duplicate()

	similar_bank_transactions = get_similar_bank_transactions(first_unpaired_expense.name, first_unpaired_expense.id, 5)

	return render(
		request,
		'pairing.html',
		{
			'kind': kind,
			'expense': first_unpaired_expense,
			'same_amount_suggestions': same_amount_suggestions,
			'similar_date_suggestions': similar_date_suggestions,
			'transaction_creation_form': YnabTransactionCreationForm(
				budget_id=budget_id, initial={'bank_expense_id': first_unpaired_expense.id}
			),
'potential_duplicate': potential_duplicate,
			'similar_bank_transactions': similar_bank_transactions,
		},
	)