# Generated by Django 5.2 on 2025-05-23 16:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_create_bank_transactions_fts_20250523_1421'),
    ]

    operations = [
        migrations.AlterField(
            model_name='banktransaction',
            name='ynab_transaction_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.ynabtransaction'),
        ),
    ]
