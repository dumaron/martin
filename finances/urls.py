from django.urls import path
from .views import *

urlpatterns = [
    path("", expenses_pairing_view, name="expenses_pairing_view"),
    path("pairing-v2", pairing_view_v2, name="pairing_v2"),
    path("pair-expense-transaction", pair_expense_with_ynab_transaction, name="pair-expense-transaction"),
    path("expenses/<int:bankexpense_id>/snooze", snooze_bankexpense, name="snooze-expense"),

    # ynab synchronizations
    path('ynab-synchronizations', ynab_synchronizations_list, name='ynab-synchronizations-list'),
    path("ynab-sync", ynab_sync, name="ynab-sync"),
    path('sync-ynab-categories', synchronize_ynab_categories, name='synchronize_ynab_categories'),

    # files
    path("file-import", file_import, name="file-import"),
]
    