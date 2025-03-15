from .schemas import YnabTransactionCreationResponse, YnabTransactionListResponse, YnabTransactionListData, ExternalYnabTransaction
import settings
import requests
import json
from itertools import chain
from datetime import datetime

from settings import YNAB_ACCOUNT_ID

is_development = settings.ENVIRONMENT == 'development'
base_url = f'https://api.ynab.com/v1/budgets/{settings.YNAB_DEFAULT_BUDGET}'
headers = {
    'Authorization': f'Bearer {settings.YNAB_API_TOKEN}',
    'Content-Type': 'application/json'
}


def get_uncleared_expenses(server_knowledge) -> YnabTransactionListData:
    """
    Fetch and validate uncleared expenses from YNAB API
    """

    response = requests.get(
        url=f'{base_url}/transactions?since_date=2023-08-01&last_knowledge_of_server={server_knowledge}',
        headers=headers
    )

    response.raise_for_status()

    response_data = response.json()
    validated_response = YnabTransactionListResponse(**response_data)
    return validated_response.data


def clear_transaction(transaction, amount=None):
    data = {
        'transaction': {
            'account_id': str(transaction.account_id),
            'cleared': transaction.ClearedStatuses.CLEARED,
        }
    }

    if amount is not None:
        # YNAB APIs receive amounts in milli-units
        data['transaction']['amount'] = int(amount * 1000)

    response = requests.put(
        url=f'{base_url}/transactions/{str(transaction.id)}',
        headers=headers,
        data=json.dumps(data)
    )

    response.raise_for_status()

    return response.json()


def get_categories():
    """
    Upsert all YNAB categories on local database
    """

    response = requests.get(
        f'{base_url}/categories',
        headers=headers
    )

    response.raise_for_status()

    data = response.json()['data']
    categories = list(chain.from_iterable(map(lambda x: x['categories'], data['category_groups'])))

    return categories


def create_transaction(amount, date, memo, ynab_category) -> ExternalYnabTransaction:
    """
    Creates a YNAB transactions on the YNAB remote database through API
    """

    data = {
        'transaction': {
            'amount': int(amount * 1000),
            'date': datetime.strftime(date, '%Y-%m-%d'),
            'approved': True,
            'cleared': 'cleared',
            'memo': memo,
            'category_id': str(ynab_category.id),
            'deleted': False,
            'account_id': YNAB_ACCOUNT_ID,
        }}

    response = requests.post(
        f'{base_url}/transactions',
        headers=headers,
        data=json.dumps(data)
    )

    response.raise_for_status()

    validated_response = YnabTransactionCreationResponse(**response.json())

    return validated_response.data.transaction