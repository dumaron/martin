from django.urls import path
from .views import expenses_pairing_view, ynab_sync, debug, pair_expense_with_ynab_transaction


urlpatterns = [
    path("", expenses_pairing_view, name="expenses_pairing_view"),
    path("ynab-sync", ynab_sync, name="ynab-sync"),
    path("debug", debug, name="debug"),
    path("pair-expense-transaction", pair_expense_with_ynab_transaction, name="pair-expense-transaction")
]
