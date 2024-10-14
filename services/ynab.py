from django.template.context_processors import static

from martin import settings
import requests
from datetime import datetime
import json

is_development = settings.ENVIRONMENT == 'development'
base_url = 'https://api.ynab.com/v1'
long_time_ago = datetime(2023, 1, 1).date()


class YNABService:
    @staticmethod
    def get_uncleared_expenses(start_from):
        date = start_from if start_from is not None else long_time_ago
        budgets = requests.get(
            f'{base_url}/budgets/{settings.YNAB_DEFAULT_BUDGET}/transactions?since_date={date.strftime("%Y-%m-%d")}',
            headers={'Authorization': 'Bearer ' + settings.YNAB_API_TOKEN})
        return budgets.json()

    @staticmethod
    def clear_transaction(transaction, amount=None):

        data = {
            'transaction': {
                'account_id': str(transaction.account_id),
                'cleared': transaction.ClearedStatuses.CLEARED,
            }
        }

        if amount is not None:
            # YNAB APIs receive amounts in milliunits
            data['transaction']['amount'] = int(amount * 1000)

        json_object = json.dumps(data, indent=4)
        url = f'{base_url}/budgets/{settings.YNAB_DEFAULT_BUDGET}/transactions/{str(transaction.id)}'

        if is_development:
            print(json_object)
            return { 'data': data }

        response = requests.put(
            url,
            headers={
                'Authorization': 'Bearer ' + settings.YNAB_API_TOKEN,
                'Content-Type': 'application/json'
            },
            data=json_object
        )

        return response.json()

    @staticmethod
    def sync_categories():
        """
        Upsert all YNAB categories on local database
        """
        pass


ynab = YNABService()
