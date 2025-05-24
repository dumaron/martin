from django.contrib import admin
from django.urls import include, path

from apps.website.views import (
   bank_transaction_detail,
   bank_transaction_list,
   create_ynab_transaction,
   file_import,
   martin_home_page,
   pair_expense_with_ynab_transaction,
   pairing_view,
   snooze_bankexpense,
   synchronize_ynab_categories,
   ynab_sync,
   ynab_synchronizations_list,
   ynab_transaction_detail,
)

urlpatterns = [
   path('', martin_home_page, name='martin_home_page'),
   path('admin/', admin.site.urls),
   path('accounts/', include('django.contrib.auth.urls')),
   path('finances/', include([
      path('<str:kind>/pairing', pairing_view, name='pairing'),

      # pages


      # mutations
      path('pair-expense-transaction', pair_expense_with_ynab_transaction, name='pair-expense-transaction'),
      path('<str:kind>/create-ynab-transaction', create_ynab_transaction, name='create-ynab-transaction'),
      path('expenses/<int:bankexpense_id>/snooze', snooze_bankexpense, name='snooze-expense'),

      # ynab synchronizations
      path('ynab-synchronizations', ynab_synchronizations_list, name='ynab-synchronizations-list'),
      path('ynab-sync', ynab_sync, name='ynab-sync'),
      path('sync-ynab-categories', synchronize_ynab_categories, name='synchronize_ynab_categories'),

      # file import for personal bank expenses
      path('file-import', file_import, name='file_import'),

      # Low-level entities
      path('bank_transactions', bank_transaction_list, name='bank_transaction_list'),
      path('bank_transactions/<int:bank_transaction_id>', bank_transaction_detail, name='bank_transaction_detail'),
      path('ynab_transactions/<str:ynab_transaction_id>', ynab_transaction_detail, name='ynab_transaction_detail'),
   ])),
]
