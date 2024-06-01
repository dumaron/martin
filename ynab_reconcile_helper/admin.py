from django.contrib import admin
from .models import BankExpense, BankFileImport, YnabImport, YnabTransaction


class BankExpenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'date']


class YnabTransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'amount', 'memo', 'cleared', 'deleted']
    list_filter = ['date', 'cleared', 'deleted']
    search_fields = ['memo']


admin.site.register(BankFileImport)
admin.site.register(BankExpense, BankExpenseAdmin)
admin.site.register(YnabImport)
admin.site.register(YnabTransaction, YnabTransactionAdmin)
