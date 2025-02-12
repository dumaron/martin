from django.urls import path
from .views import *

urlpatterns = [
    path('pairing', pairing_view, name='pairing'),

    # mutations
    path('pair-expense-transaction', pair_expense_with_ynab_transaction, name='pair-expense-transaction'),
    path('create-ynab-transaction', create_ynab_transaction, name='create-ynab-transaction'),
    path('expenses/<int:bankexpense_id>/snooze', snooze_bankexpense, name='snooze-expense'),

    # ynab synchronizations
    path('ynab-synchronizations', ynab_synchronizations_list, name='ynab-synchronizations-list'),
    path('ynab-sync', ynab_sync, name='ynab-sync'),
    path('sync-ynab-categories', synchronize_ynab_categories, name='synchronize_ynab_categories'),

    # files
    path('file-import', file_import, name='file-import'),
]
    