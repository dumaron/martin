from django.core.management.base import BaseCommand, CommandError
from tasks.models import Todo
from django.db.models import Q
from datetime import datetime, date

class Command(BaseCommand):
    help = 'TODO'

    def handle(self, *args, **options):
        valid_todos = Todo.objects.filter(
            Q(valid_from__lte=datetime.now()) | Q(valid_from__isnull=True),
            Q(status=Todo.Statuses.TODO) | Q(status=Todo.Statuses.ACTIVE))

        for todo in valid_todos:
            delta = date.today() - todo.last_increase
            priority_increase = todo.daily_priority_increase * delta.days

            if priority_increase > 0:
                todo.priority += priority_increase

            todo.last_increase = date.today()
            todo.save()