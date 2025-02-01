from finances.actions.sync_ynab_transactions import sync_ynab_transactions
from finances.adapters.ynab import create_transaction


def create_ynab_transaction_from_bank_expense(bank_expense, memo, ynab_category):
    amount = bank_expense.amount
    date = bank_expense.date
    # 1. Create the transaction on YNAB database. The transaction is already cleared
    remote_transaction = create_transaction(amount, date, memo, ynab_category)

    # 2. Update the local bank expense with the YNAB transaction id
    bank_expense.ynab_transaction_id = remote_transaction.id
    bank_expense.save()

    # 3. Sync the YNAB transactions with the local database so that we can be sure the new transaction is available
    sync_ynab_transactions(partial=False, user=bank_expense.user)

    return remote_transaction
