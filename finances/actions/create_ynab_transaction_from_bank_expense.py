from finances.adapters.ynab import YnabAdapter


def create_ynab_transaction_from_bank_expense(bank_expense, memo, ynab_category):
    amount = bank_expense.amount
    date = bank_expense.date

    remote_transaction = YnabAdapter.create_transaction(amount, date, memo, ynab_category)

    print(remote_transaction)

    pass