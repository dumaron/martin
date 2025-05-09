from datetime import datetime

from core.integrations.ynab import create_transaction
from core.mutations.sync_ynab_transactions import sync_ynab_transactions
from core.models import YnabAccount


def create_ynab_transaction_from_bank_expense(budget_id, bank_transaction, memo, ynab_category):
	"""
	Creates a YNAB transaction from a bank expense and pairs them together
	"""

	amount = bank_transaction.amount
	date = bank_transaction.date

	account = YnabAccount.objects.filter(linked_bank_account=bank_transaction.bank_account).first()
	if not account:
		raise Exception(f'No YNAB account found for bank account {bank_transaction.bank_account}')

	# 1. Create the transaction on YNAB remote database. The transaction is already cleared
	remote_transaction = create_transaction(budget_id, account.id, amount, date, memo, ynab_category)

	# 2. Pair the local bank expense with the YNAB transaction id
	bank_transaction.ynab_transaction_id = remote_transaction.id
	bank_transaction.paired_on = datetime.now()
	bank_transaction.save()

	# 3. Sync the YNAB transactions with the local database so that we can be sure the new transaction is available
	sync_ynab_transactions(budget_id, partial=True)

	return remote_transaction
