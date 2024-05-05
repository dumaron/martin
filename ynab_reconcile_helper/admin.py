from django.contrib import admin
from .models import BankExpense, BankFileImport, YnabImport, YnabTransaction


class BankExpenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'date']


admin.site.register(BankFileImport)
admin.site.register(BankExpense, BankExpenseAdmin)
admin.site.register(YnabImport)
admin.site.register(YnabTransaction)
