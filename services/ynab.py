from martin import settings
import requests
from datetime import datetime
import json

base_url = 'https://api.ynab.com/v1'
long_time_ago = datetime(2023, 1, 1).date()


class YNABService:
    @staticmethod
    def get_uncleared_expenses(start_from):
        date = start_from if start_from != None else long_time_ago
        budgets = requests.get(
            f'{base_url}/budgets/{settings.YNAB_DEFAULT_BUDGET}/transactions?since_date={date.strftime("%Y-%m-%d")}',
            headers={'Authorization': 'Bearer ' + settings.YNAB_API_TOKEN})
        return budgets.json()

    @staticmethod
    def clear_transaction(transaction):
        data = {
            'transaction': {
                'account_id': str(transaction.account_id),
                'cleared': transaction.ClearedStatuses.CLEARED,
            }}
        json_object = json.dumps(data, indent=4)
        url = f'{base_url}/budgets/{settings.YNAB_DEFAULT_BUDGET}/transactions/{str(transaction.id)}'

        response = requests.put(
            url,
            headers={
                'Authorization': 'Bearer ' + settings.YNAB_API_TOKEN,
                'Content-Type': 'application/json'
            },
            data=json_object
        )
        return response.json()


ynab = YNABService()
