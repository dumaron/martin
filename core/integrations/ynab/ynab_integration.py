import json
from datetime import datetime
from itertools import chain

import requests

import settings

from .schemas import (
	ExternalYnabTransaction,
	YnabTransactionCreationResponse,
	YnabTransactionListData,
	YnabTransactionListResponse,
)

is_development = settings.ENVIRONMENT == 'development'
base_url = 'https://api.ynab.com/v1/budgets'
headers = {'Authorization': f'Bearer {settings.YNAB_API_TOKEN}', 'Content-Type': 'application/json'}


def get_uncleared_expenses(budget_id, server_knowledge) -> YnabTransactionListData:
	"""
	Fetch and validate uncleared expenses from YNAB API
	"""

	response = requests.get(
		url=f'{base_url}/{budget_id}/transactions?since_date=2023-08-01&last_knowledge_of_server={server_knowledge}',
		headers=headers,
	)

	response.raise_for_status()

	response_data = response.json()
	validated_response = YnabTransactionListResponse(**response_data)
	return validated_response.data


def clear_transaction(transaction, amount=None):
	data = {
		'transaction': {'account_id': str(transaction.account_id), 'cleared': transaction.ClearedStatuses.CLEARED}
	}

	if amount is not None:
		# YNAB APIs receive amounts in milli-units
		data['transaction']['amount'] = int(amount * 1000)

	response = requests.put(
		url=f'{base_url}/{transaction.budget_id}/transactions/{str(transaction.id)}',
		headers=headers,
		data=json.dumps(data),
	)

	response.raise_for_status()

	return response.json()


def get_categories(budget_id):
	"""
	Returns all YNAB categories for a specific budget
	"""

	response = requests.get(f'{base_url}/{budget_id}/categories', headers=headers)
	response.raise_for_status()
	data = response.json()['data']
	categories = list(chain.from_iterable(map(lambda x: x['categories'], data['category_groups'])))
	return categories


def create_transaction(budget_id, account_id, amount, date, memo, ynab_category) -> ExternalYnabTransaction:
	"""
	Creates a YNAB transaction on the YNAB remote database through API
	"""

	data = {
		'transaction': {
			'amount': int(amount * 1000),
			'date': datetime.strftime(date, '%Y-%m-%d'),
			'approved': True,
			'cleared': 'cleared',
			'memo': memo,
			'category_id': str(ynab_category.id),
			'account_id': str(account_id),
			'deleted': False,
		}
	}

	response = requests.post(f'{base_url}/{budget_id}/transactions', headers=headers, data=json.dumps(data))

	response.raise_for_status()

	validated_response = YnabTransactionCreationResponse(**response.json())

	return validated_response.data.transaction
