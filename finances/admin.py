from django.contrib import admin
from .models import *
from datetime import datetime


@admin.action(description="Snooze")
def snooze(modeladmin, request, queryset):
    queryset.update(snoozed_on=datetime.now())


class BankExpenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'amount', 'snoozed_on', 'paired_on', 'file_type']
    search_fields = ['name', 'amount']
    list_filter = [
        'file_import__file_type',
        ('snoozed_on', admin.EmptyFieldListFilter),
        ('paired_on', admin.EmptyFieldListFilter),
    ]
    actions = [snooze]

    def file_type(self, obj):
        return obj.file_import.file_type


class YnabTransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'amount', 'memo', 'cleared', 'deleted']
    list_filter = ['date', 'cleared', 'deleted']
    search_fields = ['memo']


class YnabImportAdmin(admin.ModelAdmin):
    list_display = ['execution_datetime', 'server_knowledge']

admin.site.register(BankFileImport)
admin.site.register(BankExpense, BankExpenseAdmin)
admin.site.register(YnabImport, YnabImportAdmin)
admin.site.register(YnabTransaction, YnabTransactionAdmin)
admin.site.register(YnabCategory)
