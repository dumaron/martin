from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.website.views import (
	bank_file_import_detail,
	bank_file_import_list,
	bank_transaction_detail,
	bank_transaction_list,
	create_ynab_transaction,
	file_import,
	link_duplicate_bank_transaction,
	martin_home_page,
	match_transactions,
	pairing_view,
	snooze_bank_transaction,
	synchronize_ynab_categories,
	ynab_sync,
	ynab_synchronizations_list,
	ynab_transaction_detail,
)

urlpatterns = [
	path('', martin_home_page, name='martin_home_page'),
	path('admin/', admin.site.urls),
	path('accounts/', include('django.contrib.auth.urls')),
	path(
		'finances/',
		include(
			[
				path('<str:kind>/pairing', pairing_view, name='pairing'),
				# mutations
				path('pair-transactions', match_transactions, name='pair-transactions'),
				path('<str:kind>/create-ynab-transaction', create_ynab_transaction, name='create-ynab-transaction'),
				path(
					'bank-transactions/<int:bank_transaction_id>/snooze', snooze_bank_transaction, name='snooze-transaction'
				),
				path(
					'bank_transactions/<int:duplicate_transaction_id>/link-duplicate',
					link_duplicate_bank_transaction,
					name='link-duplicate-bank-transaction',
				),
				# ynab synchronizations
				path('ynab-synchronizations', ynab_synchronizations_list, name='ynab-synchronizations-list'),
				path('ynab-sync', ynab_sync, name='ynab-sync'),
				path('sync-ynab-categories', synchronize_ynab_categories, name='synchronize_ynab_categories'),
				# file import for personal bank transactions
				path('file-import', file_import, name='file_import'),
				# Low-level entities
				path('bank_transactions', bank_transaction_list, name='bank_transaction_list'),
				path(
					'bank_transactions/<int:bank_transaction_id>', bank_transaction_detail, name='bank_transaction_detail'
				),
				path('bank_file_imports', bank_file_import_list, name='bank_file_import_list'),
				path(
					'bank_file_imports/<int:bank_file_import_id>', bank_file_import_detail, name='bank_file_import_detail'
				),
				path(
					'ynab_transactions/<str:ynab_transaction_id>', ynab_transaction_detail, name='ynab_transaction_detail'
				),
			]
		),
	),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
