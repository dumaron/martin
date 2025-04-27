from datetime import datetime

from core.mutations.sync_ynab_transactions import sync_ynab_transactions
from core.integrations.ynab import create_transaction
from settings.base import YNAB_PERSONAL_BUDGET_ID


def create_ynab_transaction_from_bank_expense(budget_id, bank_expense, memo, ynab_category):
	"""
	Creates a YNAB transaction from a bank expense and pairs them together
	"""

	amount = bank_expense.amount
	date = bank_expense.date

	# 1. Create the transaction on YNAB remote database. The transaction is already cleared
	remote_transaction = create_transaction(budget_id, amount, date, memo, ynab_category)

	# 2. Pair the local bank expense with the YNAB transaction id
	bank_expense.ynab_transaction_id = remote_transaction.id
	bank_expense.paired_on = datetime.now()
	bank_expense.save()

	# 3. Sync the YNAB transactions with the local database so that we can be sure the new transaction is available
	sync_ynab_transactions(budget_id, partial=False)

	return remote_transaction
