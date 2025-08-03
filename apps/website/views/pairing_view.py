from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.website.forms import YnabTransactionCreationForm
from apps.website.utils import highlight_text_differences
from core.models import BankTransaction, YnabTransaction
from settings.base import YNAB_PERSONAL_BUDGET_ID, YNAB_SHARED_BUDGET_ID


@login_required
@require_GET
def pairing_view(request, kind):
	"""
	Second version of the pairing view. It is bank transaction centric: takes the oldest unpaired bank transaction and shows
	some suggestions for pair-able YNAB transactions.
	"""

	personal = kind == 'personal'
	budget_id = YNAB_PERSONAL_BUDGET_ID if personal else YNAB_SHARED_BUDGET_ID

	first_unpaired_bank_transaction = (
		BankTransaction.objects.filter(
			snoozed_on=None, paired_on=None, duplicate_of=None, bank_account__personal=personal
		)
		# ↓ sort by ID technically not needed, but AI convinced me it's useful to avoid undeterministic behaviors during tests
		.order_by('date', 'id')
		.first()
	)

	if first_unpaired_bank_transaction is None:
		return render(request, 'pairing_empty.html', {})

	same_amount_suggestions = YnabTransaction.objects.filter(
		deleted=False,
		amount=first_unpaired_bank_transaction.amount,
		cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
		budget_id=budget_id,
	)

	similar_date_suggestions = YnabTransaction.objects.filter(
		deleted=False,
		date__lte=first_unpaired_bank_transaction.date + timedelta(days=3),
		date__gte=first_unpaired_bank_transaction.date - timedelta(days=3),
		cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
		budget_id=budget_id,
	)

	potential_duplicate = first_unpaired_bank_transaction.get_potential_duplicate()
	potential_duplicate_highlighted = None

	if potential_duplicate:
		potential_duplicate_highlighted = highlight_text_differences(
			first_unpaired_bank_transaction.name, potential_duplicate.name
		)

	return render(
		request,
		'pairing.html',
		{
			'kind': kind,
			'bank_transaction': first_unpaired_bank_transaction,
			'same_amount_suggestions': same_amount_suggestions,
			'similar_date_suggestions': similar_date_suggestions,
			'transaction_creation_form': YnabTransactionCreationForm(
				budget_id=budget_id, initial={'bank_transaction_id': first_unpaired_bank_transaction.id}
			),
			'potential_duplicate': potential_duplicate,
			'potential_duplicate_highlighted': potential_duplicate_highlighted,
		},
	)
