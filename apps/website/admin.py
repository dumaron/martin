from datetime import datetime

from django.contrib import admin

from core.models import (
    BankAccount,
    BankFileImport,
    BankTransaction,
    Event,
    Memory,
    Note,
    YnabAccount,
    YnabBudget,
    YnabCategory,
    YnabImport,
    YnabTransaction,
)


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

    def imported_on(self, obj):
        return obj.file_import.import_date



class YnabTransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'amount', 'budget', 'memo', 'cleared', 'deleted']
    list_filter = ['date', 'cleared', 'deleted', 'budget']
    search_fields = ['memo']


class YnabImportAdmin(admin.ModelAdmin):
    list_display = ['budget', 'execution_datetime', 'server_knowledge']
    list_filter = ['budget']
    

class BankFileImportAdmin(admin.ModelAdmin):
    list_display = ['id', 'file_name', 'file_type', 'import_date']


class YnabAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'id', 'budget']
    list_filter = ['budget']


class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'iban']


class MemoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'description']
    search_fields = ['description']
    list_filter = ['date']



admin.site.register(Event)
admin.site.register(Note)
admin.site.register(BankFileImport, BankFileImportAdmin)
admin.site.register(BankTransaction, BankExpenseAdmin)
admin.site.register(YnabImport, YnabImportAdmin)
admin.site.register(YnabTransaction, YnabTransactionAdmin)
admin.site.register(YnabCategory)
admin.site.register(YnabBudget)
admin.site.register(YnabAccount, YnabAccountAdmin)
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(Memory, MemoryAdmin)
