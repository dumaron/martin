# Generated by Django 5.2 on 2025-04-20 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_bankexpense_personal_account_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankfileimport',
            name='file_type',
            field=models.CharField(choices=[('UNICREDIT_BANK_ACCOUNT_CSV_EXPORT', 'Unicredit Bank Account Csv Export'), ('FINECO_BANK_ACCOUNT_XLSX_EXPORT', 'Fineco Bank Account Xslx Export'), ('UNICREDIT_DEBIT_CARD_CSV_EXPORT', 'Unicredit Debit Card Csv Export'), ('CREDEM_CSV_EXPORT', 'Credem Csv Export')], default='UNICREDIT_BANK_ACCOUNT_CSV_EXPORT', max_length=255),
        ),
    ]
