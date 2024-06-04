from django.contrib import admin
from .models import BankExpense, BankFileImport, YnabImport, YnabTransaction
from datetime import datetime


@admin.action(description="Snooze")
def snooze(modeladmin, request, queryset):
    queryset.update(snoozed_on=datetime.now())


class BankExpenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'amount', 'snoozed_on', 'paired_on', 'ynab_transaction_id']
    search_fields = ['name', 'amount']
    actions = [snooze]


class YnabTransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'amount', 'memo', 'cleared', 'deleted']
    list_filter = ['date', 'cleared', 'deleted']
    search_fields = ['memo']


admin.site.register(BankFileImport)
admin.site.register(BankExpense, BankExpenseAdmin)
admin.site.register(YnabImport)
admin.site.register(YnabTransaction, YnabTransactionAdmin)
