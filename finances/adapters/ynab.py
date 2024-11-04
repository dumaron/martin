from finances.models import YnabTransaction
from martin import settings
import requests
import json
from itertools import chain
from datetime import datetime

from martin.settings import YNAB_ACCOUNT_ID

is_development = settings.ENVIRONMENT == 'development'
base_url = 'https://api.ynab.com/v1'


class YnabAdapter:
    @staticmethod
    def get_uncleared_expenses(server_knowledge):
        budgets = requests.get(
            f'{base_url}/budgets/{settings.YNAB_DEFAULT_BUDGET}/transactions?since_date=2023-08-01&last_knowledge_of_server={server_knowledge}',
            headers={'Authorization': 'Bearer ' + settings.YNAB_API_TOKEN})
        # TODO find a way to validate this response with pydantic
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
            return {'data': data}

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
    def get_categories():
        """
        Upsert all YNAB categories on local database
        """

        response = requests.get(
            f'{base_url}/budgets/{settings.YNAB_DEFAULT_BUDGET}/categories',
            headers={'Authorization': 'Bearer ' + settings.YNAB_API_TOKEN})

        data = response.json()['data']
        categories = list(chain.from_iterable(map(lambda x: x['categories'], data['category_groups'])))

        return categories


    @staticmethod
    def create_transaction(amount, date, memo, ynab_category):
        """
        Creates a YNAB transactions through API
        """

        data = {
            'transaction': {
                'amount': int(amount * 1000),
                'date': datetime.strftime(date, '%Y-%m-%d'),
                'approved': True,
                'cleared': YnabTransaction.ClearedStatuses.CLEARED,
                'memo': memo,
                'category_id': str(ynab_category.id),
                'deleted': False,
                'account_id': YNAB_ACCOUNT_ID,
            }}

        json_object = json.dumps(data, indent=4)
        url = f'{base_url}/budgets/{settings.YNAB_DEFAULT_BUDGET}/transactions'

        # if is_development:
        #     print(json_object)
        #     return { 'data': data }

        response = requests.post(
            url,
            headers={
                'Authorization': 'Bearer ' + settings.YNAB_API_TOKEN,
                'Content-Type': 'application/json'
            },
            data=json_object
        )

        return response.json()
