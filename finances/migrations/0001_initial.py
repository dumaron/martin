# Generated by Django 5.0.3 on 2024-03-22 14:49

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BankFileImport",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("file_name", models.CharField(max_length=255)),
                ("bank_file", models.FileField(upload_to="uploads/")),
                ("import_date", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BankExpense",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=1024)),
                ("date", models.DateField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "file_import",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="finances.bankfileimport",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="bankexpense",
            constraint=models.UniqueConstraint(
                models.F("name"),
                models.F("date"),
                models.F("amount"),
                name="expense-uniqueness-name-date-amount",
            ),
        ),
    ]
