from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('tasks', '0018_alter_dailysuggestion_table_and_more'),
        ('core', '0003_add_task_models'),  # Ensure core models are created first
    ]

    state_operations = [
        migrations.RemoveField(
            model_name='dailysuggestion',
            name='added_todos',
        ),
        migrations.RemoveField(
            model_name='dailysuggestion',
            name='picked_todos',
        ),
        migrations.RemoveField(
            model_name='dailysuggestionaddedtodo',
            name='suggestion',
        ),
        migrations.RemoveField(
            model_name='dailysuggestionaddedtodo',
            name='todo',
        ),
        migrations.RemoveField(
            model_name='dailysuggestionpickedtodo',
            name='suggestion',
        ),
        migrations.RemoveField(
            model_name='dailysuggestionpickedtodo',
            name='todo',
        ),
        migrations.DeleteModel(
            name='DailySuggestionAddedTodo',
        ),
        migrations.DeleteModel(
            name='DailySuggestionPickedTodo',
        ),
        migrations.DeleteModel(
            name='DailySuggestion',
        ),
        migrations.RemoveField(
            model_name='todo',
            name='project',
        ),
        migrations.RemoveField(
            model_name='update',
            name='project',
        ),
        migrations.RemoveField(
            model_name='waiting',
            name='project',
        ),
        migrations.DeleteModel(
            name='Todo',
        ),
        migrations.DeleteModel(
            name='Update',
        ),
        migrations.DeleteModel(
            name='Waiting',
        ),
        migrations.DeleteModel(
            name='Inbox',
        ),
        migrations.DeleteModel(
            name='Project',
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations,
            database_operations=[],
        ),
    ]