from datetime import datetime

from core.integrations.ynab import create_transaction
from core.models import YnabAccount, YnabTransaction
from core.mutations.sync_ynab_transactions import sync_ynab_transactions


def create_ynab_transaction_from_bank_transaction(budget_id, bank_transaction, memo, ynab_category) -> None:
	"""
	Creates a YNAB transaction from a bank transaction and matches them together
	"""

	amount = bank_transaction.amount
	date = bank_transaction.date

	account = YnabAccount.objects.filter(linked_bank_account=bank_transaction.bank_account).first()
	if not account:
		raise Exception(f'No YNAB account found for bank account {bank_transaction.bank_account}')

	# 1. Create the transaction on YNAB remote database. The transaction is already cleared
	remote_transaction = create_transaction(budget_id, account.id, amount, date, memo, ynab_category)

	# 2. Sync the YNAB transactions with the local database so that we can be sure the new transaction is available
	# I'm not super-happy about having to perform a partial refresh on every create, as it might make the creation action
	# more complex than it should be. In my mind, I would have just created a local version of the YNAB transaction just
	# created.
	# However, due to some choices about the model, this would miss a YNAB import, which is required...
	# The most pragmatic choice is to just trigger a refresh, being somewhat confident that the newly created transaction
	# will be there.
	sync_ynab_transactions(budget_id, partial=True)
	local_ynab_transaction = YnabTransaction.objects.filter(id=remote_transaction.id).first()

	# 3. Pair the local bank transaction with the YNAB transaction id
	bank_transaction.matched_ynab_transaction = local_ynab_transaction
	bank_transaction.paired_on = datetime.now()
	bank_transaction.save()

	return
