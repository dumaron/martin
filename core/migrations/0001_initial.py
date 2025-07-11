# Generated by Django 5.2.3 on 2025-06-28 16:50

import datetime
import django.db.models.deletion
from django.db import migrations, models

#
# I also needed to run the following query to clean up a bit the migrations table, which was a mess:
# DELETE FROM django_migrations
# WHERE app IN ('finances', 'tasks', 'memory', 'martin')
# OR (app = 'core' AND name <> '0001_initial');

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('iban', models.CharField(max_length=34)),
                ('personal', models.BooleanField()),
            ],
            options={
                'db_table': 'bank_accounts',
            },
        ),
        migrations.CreateModel(
            name='BankFileImport',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('file_name', models.CharField(max_length=255)),
                ('file_type', models.CharField(choices=[('UNICREDIT_BANK_ACCOUNT_CSV_EXPORT', 'Unicredit Bank Account Csv Export'), ('FINECO_BANK_ACCOUNT_XLSX_EXPORT', 'Fineco Bank Account Xslx Export'), ('UNICREDIT_DEBIT_CARD_CSV_EXPORT', 'Unicredit Debit Card Csv Export'), ('CREDEM_CSV_EXPORT', 'Credem Csv Export')], default='UNICREDIT_BANK_ACCOUNT_CSV_EXPORT', max_length=255)),
                ('bank_file', models.FileField(upload_to='uploads/')),
                ('import_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'bank_file_imports',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('date', models.DateField(default=datetime.date.today)),
                ('time', models.TimeField(blank=True, default=datetime.datetime.now, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'events',
            },
        ),
        migrations.CreateModel(
            name='Memory',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('photo', models.FileField(upload_to='memories/')),
                ('description', models.TextField(blank=True)),
                ('location', models.CharField(blank=True, max_length=256, null=True)),
                ('date', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'memories',
                'db_table': 'memories',
            },
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'notes',
            },
        ),
        migrations.CreateModel(
            name='YnabBudget',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
            ],
            options={
                'db_table': 'ynab_budgets',
            },
        ),
        migrations.CreateModel(
            name='YnabAccount',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('linked_bank_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.bankaccount')),
                ('budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ynabbudget')),
            ],
            options={
                'db_table': 'ynab_accounts',
            },
        ),
        migrations.CreateModel(
            name='YnabCategory',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('hidden', models.BooleanField()),
                ('category_group_name', models.CharField(max_length=1024)),
                ('budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ynabbudget')),
            ],
            options={
                'verbose_name_plural': 'ynab categories',
                'db_table': 'ynab_categories',
            },
        ),
        migrations.CreateModel(
            name='YnabImport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('execution_datetime', models.DateTimeField()),
                ('server_knowledge', models.IntegerField(blank=True, null=True)),
                ('budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ynabbudget')),
            ],
            options={
                'db_table': 'ynab_imports',
            },
        ),
        migrations.CreateModel(
            name='YnabTransaction',
            fields=[
                ('id', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('amount', models.FloatField()),
                ('memo', models.CharField(blank=True, max_length=512, null=True)),
                ('approved', models.BooleanField()),
                ('cleared', models.CharField(choices=[('cleared', 'Cleared'), ('uncleared', 'Uncleared'), ('reconciled', 'Reconciled')], max_length=10)),
                ('flag_color', models.CharField(blank=True, choices=[('red', 'Red'), ('orange', 'Orange'), ('yellow', 'Yellow'), ('green', 'Green'), ('blue', 'Blue'), ('purple', 'Purple')], max_length=6, null=True)),
                ('flag_name', models.CharField(blank=True, max_length=64, null=True)),
                ('payee_id', models.UUIDField(blank=True, null=True)),
                ('category_id', models.UUIDField(blank=True, null=True)),
                ('transfer_account_id', models.UUIDField(blank=True, null=True)),
                ('transfer_transaction_id', models.CharField(blank=True, max_length=64, null=True)),
                ('matched_transaction_id', models.CharField(blank=True, max_length=64, null=True)),
                ('import_id', models.CharField(blank=True, max_length=64, null=True)),
                ('import_payee_name', models.CharField(blank=True, max_length=256, null=True)),
                ('import_payee_original', models.CharField(blank=True, max_length=256, null=True)),
                ('debt_transaction_type', models.CharField(blank=True, choices=[('payment', 'Payment'), ('refund', 'Refund'), ('fee', 'Fee'), ('interest', 'Interest'), ('escrow', 'Escrow'), ('balanceAdjustment', 'Balance Adjustment'), ('credit', 'Credit'), ('charge', 'Charge')], max_length=17, null=True)),
                ('deleted', models.BooleanField()),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.ynabaccount')),
                ('budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ynabbudget')),
                ('local_import', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ynabimport')),
            ],
            options={
                'db_table': 'ynab_transactions',
            },
        ),
        migrations.CreateModel(
            name='BankTransaction',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=1024)),
                ('date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('paired_on', models.DateTimeField(blank=True, null=True)),
                ('snoozed_on', models.DateTimeField(blank=True, null=True)),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.bankaccount')),
                ('file_import', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.bankfileimport')),
                ('matched_ynab_transaction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.ynabtransaction')),
            ],
            options={
                'db_table': 'bank_transactions',
                'constraints': [models.UniqueConstraint(models.F('name'), models.F('date'), models.F('amount'), name='expense-uniqueness-name-date-amount')],
            },
        ),
    ]
