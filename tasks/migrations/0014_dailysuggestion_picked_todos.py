# Generated by Django 5.1.3 on 2024-12-25 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0013_dailysuggestion_reviewed_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailysuggestion',
            name='picked_todos',
            field=models.ManyToManyField(blank=True, related_name='picked_todos', to='tasks.todo'),
        ),
    ]
