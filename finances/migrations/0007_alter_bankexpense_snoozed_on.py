# Generated by Django 5.0.4 on 2024-06-04 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0006_bankexpense_snoozed_on'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankexpense',
            name='snoozed_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]