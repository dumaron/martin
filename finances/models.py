from django.db import models
from django.contrib.auth import get_user_model
from finances.adapters.file_reader import get_file_rows
from datetime import datetime
from .utils import fix_unicredit_floating_point

User = get_user_model()


class BankFileImport(models.Model):

    class FileType(models.TextChoices):
        UNICREDIT_BANK_ACCOUNT_CSV_EXPORT = 'UNICREDIT_BANK_ACCOUNT_CSV_EXPORT'
        FINECO_BANK_ACCOUNT_XSLX_EXPORT = 'FINECO_BANK_ACCOUNT_XLSX_EXPORT'
        UNICREDIT_DEBIT_CARD_CSV_EXPORT = 'UNICREDIT_DEBIT_CARD_CSV_EXPORT'

    id = models.AutoField(primary_key=True)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=255, choices=FileType, default=FileType.UNICREDIT_BANK_ACCOUNT_CSV_EXPORT)
    bank_file = models.FileField(upload_to='uploads/')
    import_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.file_name
    
    def save(self, *args, **kwargs):
        imported = super().save(*args, **kwargs)

        file_parsing_strategy = None
        if self.file_type == BankFileImport.FileType.UNICREDIT_BANK_ACCOUNT_CSV_EXPORT:
            file_parsing_strategy = BankExpense.from_unicredit_bank_account_csv_row
        elif self.file_type == BankFileImport.FileType.UNICREDIT_DEBIT_CARD_CSV_EXPORT:
            file_parsing_strategy = BankExpense.from_unicredit_debit_card_csv_row
        elif self.file_type == BankFileImport.FileType.FINECO_BANK_ACCOUNT_XSLX_EXPORT:
            file_parsing_strategy = BankExpense.from_fineco_bank_account_xslx_row

        if file_parsing_strategy is None:
            # not yet implemented, nothing to do
            return imported

        # When saving, we want it also to create many single expense entries as per file
        rows = get_file_rows(self.bank_file, self.file_type)
        expenses = [file_parsing_strategy(row, self.user, self) for row in rows]

        # Given that we have a unique constraint based on SQL based on name, date and amount, the already-imported
        # expenses will trigger an error. However, by using `ignore_conflicts`, we can just simulate a behaviour where
        # the duplicates are just skipped
        BankExpense.objects.bulk_create(expenses, ignore_conflicts=True)
        return imported


class BankExpense(models.Model):
    id = models.AutoField(primary_key=True)
    file_import = models.ForeignKey(BankFileImport, on_delete=models.CASCADE)
    name = models.CharField(max_length=1024)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ynab_transaction_id = models.CharField(max_length=256, null=True, blank=True)
    paired_on = models.DateTimeField(null=True, blank=True)
    snoozed_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = models.UniqueConstraint('name', 'date', 'amount', name='expense-uniqueness-name-date-amount'),
    
    @classmethod
    def from_unicredit_bank_account_csv_row(cls, row, user, file_import):
        return BankExpense(
            name=row['Descrizione'].strip(),
            amount=fix_unicredit_floating_point(row['Importo (EUR)']),
            user=user,
            date=datetime.strptime(row['Data Registrazione'], '%d.%m.%Y'),
            file_import=file_import
        )

    @classmethod
    def from_unicredit_debit_card_csv_row(cls, row, user, file_import):
        return BankExpense(
            name=row['Descrizione'].strip(),
            amount=fix_unicredit_floating_point(row['Importo']),
            user=user,
            date=datetime.strptime(row['Data Registrazione'], '%d/%m/%Y'),
            file_import=file_import
        )

    @classmethod
    def from_fineco_bank_account_xslx_row(cls, row, user, file_import):
        return BankExpense(
            name=row['Descrizione_Completa'].strip(),
            amount=float(row['Entrate'] or 0) + float(row['Uscite'] or 0),
            user=user,
            date=datetime.strptime(row['Data'], '%d/%m/%Y'),
            file_import=file_import
        )

    def __str__(self):
        return self.name


class YnabImport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    execution_datetime = models.DateTimeField()
    server_knowledge = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f'YNAB import of {datetime.strftime(self.execution_datetime, '%d/%m/%Y %H:%M %Z')}'


class YnabTransaction(models.Model):

    class ClearedStatuses(models.TextChoices):
        CLEARED = 'cleared'
        UNCLEARED = 'uncleared'
        RECONCILED = 'reconciled'

    class FlagColors(models.TextChoices):
        RED = 'red'
        ORANGE = 'orange'
        YELLOW = 'yellow' # shared with Federica using the official ratio (70/30)
        GREEN = 'green'
        BLUE = 'blue'
        PURPLE = 'purple'

    class TransactionTypes(models.TextChoices):
        PAYMENT = 'payment'
        REFUND = 'refund'
        FEE = 'fee'
        INTEREST = 'interest'
        ESCROW = 'escrow'
        BALANCE_ADJUSTMENT = 'balanceAdjustment'
        CREDIT = 'credit'
        CHARGE = 'charge'

    id = models.CharField(primary_key=True, max_length=64)
    date = models.DateField()
    amount = models.FloatField()
    memo = models.CharField(null=True, blank=True, max_length=512)
    approved = models.BooleanField()
    cleared = models.CharField(choices=ClearedStatuses, max_length=10)
    flag_color = models.CharField(null=True, blank=True, choices=FlagColors, max_length=6)
    flag_name = models.CharField(null=True, blank=True, max_length=64)
    account_id = models.UUIDField(null=True, blank=True)
    payee_id = models.UUIDField(null=True, blank=True)
    category_id = models.UUIDField(null=True, blank=True)
    transfer_account_id = models.UUIDField(null=True, blank=True)
    transfer_transaction_id = models.CharField(null=True, blank=True, max_length=64)
    matched_transaction_id = models.CharField(null=True, blank=True, max_length=64)
    import_id = models.CharField(null=True, blank=True, max_length=64)
    import_payee_name = models.CharField(null=True, blank=True, max_length=256)
    import_payee_original = models.CharField(null=True, blank=True, max_length=256)
    debt_transaction_type = models.CharField(null=True, blank=True, choices=TransactionTypes, max_length=17)
    deleted = models.BooleanField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    local_import = models.ForeignKey(YnabImport, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.amount} {self.date} {self.memo}'


class YnabCategory(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=256)
    hidden = models.BooleanField()
    category_group_name = models.CharField(max_length=1024)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name