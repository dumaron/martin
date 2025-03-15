from django.contrib import admin
from django.urls import path, include

from apps.website.views import create_ynab_transaction, file_import, martin_home_page, \
   pair_expense_with_ynab_transaction, pairing_view, \
   snooze_bankexpense, synchronize_ynab_categories, ynab_sync, ynab_synchronizations_list

urlpatterns = [
   path('', martin_home_page, name='martin_home_page'),
   path('admin/', admin.site.urls),
   path('accounts/', include('django.contrib.auth.urls')),
   path('finances/', include([
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
   ])),
]
