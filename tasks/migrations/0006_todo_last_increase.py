# Generated by Django 5.1.1 on 2024-10-20 12:08

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_todo_inbox_after_completion'),
    ]

    operations = [
        migrations.AddField(
            model_name='todo',
            name='last_increase',
            field=models.DateField(default=datetime.date.today),
        ),
    ]