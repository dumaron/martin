# Generated by Django 5.0.3 on 2024-04-06 06:23

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "finances",
            "0004_ynabexpense_user_ynabimport_ynabexpense_local_import",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name="YnabExpense",
            new_name="YnabTransaction",
        ),
    ]