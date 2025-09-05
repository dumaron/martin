from apps.website.views.create_ynab_transaction import create_ynab_transaction
from apps.website.views.file_import import file_import
from apps.website.views.home import martin_home_page
from apps.website.views.inbox_processing import flow_page, inbox_create, process_inbox_item
from apps.website.views.link_duplicate_bank_transaction import link_duplicate_bank_transaction
from apps.website.views.pair_expense import match_transactions
from apps.website.views.pairing_view import pairing_view
from apps.website.views.projects import project_create, project_detail, project_list, project_update_status
from apps.website.views.snooze_bank_transaction import snooze_bank_transaction
from apps.website.views.synchronize_ynab_categories import synchronize_ynab_categories
from apps.website.views.tasks import simple_tasks, task_create, task_mark_aborted, task_mark_done
from apps.website.views.transactions import (
	BankTransactionTable,
	bank_file_import_detail,
	bank_file_import_list,
	bank_transaction_detail,
	bank_transaction_list,
	ynab_transaction_detail,
)
from apps.website.views.ynab_sync import ynab_sync
from apps.website.views.ynab_synchronizations_list import ynab_synchronizations_list

__all__ = [
	'martin_home_page',
	'pairing_view',
	'match_transactions',
	'snooze_bank_transaction',
	'create_ynab_transaction',
	'file_import',
	'ynab_sync',
	'ynab_synchronizations_list',
	'synchronize_ynab_categories',
	'bank_file_import_detail',
	'bank_file_import_list',
	'bank_transaction_detail',
	'bank_transaction_list',
	'ynab_transaction_detail',
	'BankTransactionTable',
	'link_duplicate_bank_transaction',
	'project_list',
	'project_detail',
	'project_create',
	'project_update_status',
	'simple_tasks',
	'task_create',
	'task_mark_aborted',
	'task_mark_done',
	'inbox_create',
	'flow_page',
	'process_inbox_item',
]
