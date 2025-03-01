from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_bankfileimport_ynabcategory_ynabimport_and_more'),
    ]

    state_operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('status', models.CharField(choices=[('active', 'Active'), ('archived', 'Archived'), ('deleted', 'Deleted')], max_length=32)),
                ('treenode_display_field', models.CharField(max_length=1024)),
            ],
            options={
                'db_table': 'projects',
                'verbose_name': 'Project',
                'verbose_name_plural': 'Projects',
            },
            bases=('treenode.treenode',),
        ),
        migrations.CreateModel(
            name='Inbox',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('content', models.TextField()),
                ('context', models.TextField(choices=[('private', 'Private'), ('work', 'Work')], default='private')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'inboxes',
                'verbose_name_plural': 'inboxes',
            },
        ),
        migrations.CreateModel(
            name='Waiting',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('content', models.TextField()),
                ('status', models.CharField(choices=[('waiting', 'Waiting'), ('done', 'Done'), ('deleted', 'Deleted')], default='waiting', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=models.CASCADE, to='core.project')),
            ],
            options={
                'db_table': 'waiting',
            },
        ),
        migrations.CreateModel(
            name='Todo',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('description', models.CharField(max_length=2048)),
                ('status', models.CharField(choices=[('todo', 'Todo'), ('active', 'Active'), ('done', 'Done'), ('archived', 'Archived'), ('deleted', 'Deleted')], max_length=32)),
                ('valid_from', models.DateTimeField(blank=True, null=True)),
                ('deadline', models.DateTimeField(blank=True, null=True)),
                ('priority', models.SmallIntegerField(default=0)),
                ('daily_priority_increase', models.SmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_valid_order_pray', models.BooleanField(default=False)),
                ('inbox_after_completion', models.TextField(blank=True, null=True)),
                ('waiting_after_completion', models.TextField(blank=True, null=True)),
                ('last_increase', models.DateField(auto_now_add=True)),
                ('snoozed_until', models.DateTimeField(blank=True, null=True)),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, to='core.project')),
            ],
            options={
                'db_table': 'todos',
            },
        ),
        migrations.CreateModel(
            name='Update',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=models.CASCADE, to='core.project')),
            ],
            options={
                'db_table': 'updates',
            },
        ),
        migrations.CreateModel(
            name='DailySuggestion',
            fields=[
                ('date', models.DateField(primary_key=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'daily_suggestions',
            },
        ),
        migrations.CreateModel(
            name='DailySuggestionAddedTodo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('suggestion', models.ForeignKey(on_delete=models.CASCADE, to='core.dailysuggestion')),
                ('todo', models.ForeignKey(on_delete=models.CASCADE, to='core.todo')),
            ],
            options={
                'db_table': 'daily_suggestion_added_todos',
                'ordering': ['id'],
                'unique_together': {('suggestion', 'todo')},
            },
        ),
        migrations.CreateModel(
            name='DailySuggestionPickedTodo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('suggestion', models.ForeignKey(on_delete=models.CASCADE, to='core.dailysuggestion')),
                ('todo', models.ForeignKey(on_delete=models.CASCADE, to='core.todo')),
            ],
            options={
                'db_table': 'daily_suggestion_picked_todos',
                'ordering': ['id'],
                'unique_together': {('suggestion', 'todo')},
            },
        ),
        migrations.AddField(
            model_name='dailysuggestion',
            name='added_todos',
            field=models.ManyToManyField(related_name='added_todos', through='core.DailySuggestionAddedTodo', to='core.todo'),
        ),
        migrations.AddField(
            model_name='dailysuggestion',
            name='picked_todos',
            field=models.ManyToManyField(related_name='picked_todos', through='core.DailySuggestionPickedTodo', to='core.todo'),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations,
            database_operations=[],
        ),
    ]