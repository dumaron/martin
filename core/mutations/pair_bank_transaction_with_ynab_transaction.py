from datetime import datetime

from core.integrations.ynab import clear_transaction
from core.models import YnabTransaction


def pair_bank_transaction_with_ynab_transaction(bank_transaction, ynab_transaction, override_amount) -> None:
	"""
	Marks a YNAB transaction as "Cleared" and pairs it to a bank transaction
	"""

	# Sometimes I record transactions in YNAB with a slightly different amount of money than what it turns out to
	# be. Given that the bank transaction is _always_ the source of truth, I can decide to override the YNAB amount
	# attribute when pairing to make them match without having to do it manually through app or web interface.
	ynab_new_amount = bank_transaction.amount if override_amount else None

	# Making the ynab transaction as "Cleared" in YNAB through API. The adapter takes care of updating the amount too
	# if needed.
	clear_transaction_result = clear_transaction(ynab_transaction, ynab_new_amount)

	if clear_transaction_result['data']:
		# Updating the local representation of the ynab transaction to make it "Cleared" too
		ynab_transaction.cleared = YnabTransaction.ClearedStatuses.CLEARED

		if override_amount:
			ynab_transaction.amount = ynab_new_amount

		ynab_transaction.save()

		# Now we can finally pair the bank transaction with the cleared transaction
		bank_transaction.matched_ynab_transaction = ynab_transaction
		bank_transaction.paired_on = datetime.now()
		bank_transaction.save()
