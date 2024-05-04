from django.contrib import admin
from .models import BankExpense, BankFileImport, YnabImport, YnabTransaction

admin.site.register(BankFileImport)
admin.site.register(BankExpense)
admin.site.register(YnabImport)
admin.site.register(YnabTransaction)
