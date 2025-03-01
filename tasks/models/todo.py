from datetime import date
from django.db import models
from .project import Project
from .inbox import Inbox
from .waiting import Waiting


class Todo(models.Model):
    class Statuses(models.TextChoices):
        TODO = 'todo'
        ACTIVE = 'active'
        DONE = 'done'
        ARCHIVED = 'archived'
        DELETED = 'deleted'

    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=2048)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(choices=Statuses, max_length=32)
    valid_from = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    priority = models.SmallIntegerField(default=0)
    daily_priority_increase = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_valid_order_pray = models.BooleanField(default=False)
    inbox_after_completion = models.TextField(null=True, blank=True)
    waiting_after_completion = models.TextField(null=True, blank=True)
    last_increase = models.DateField(default=date.today)
    snoozed_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'todos'

    def save(self, *args, **kwargs):
        # If the Todo status is "Done" then there is a chance this update is to mark it done from a previous state.
        # We need to check that in order to tell if we need to run the post-completion routines
        if self.status == Todo.Statuses.DONE:
            current_todo = Todo.objects.get(pk=self.id)

            if current_todo.status == Todo.Statuses.TODO or current_todo.status == Todo.Statuses.ACTIVE:
                # Now we're sure we're handling a task that has been marked as completed just now. We can run the
                # post-completion routines.

                # Spawning new Inbox object if specified
                if self.inbox_after_completion != '':
                    inbox = Inbox(content=self.inbox_after_completion)
                    inbox.save()

                # Spawning new Waiting object if specified
                if self.waiting_after_completion != '':
                    waiting = Waiting(content=self.waiting_after_completion, project=self.project)
                    waiting.save()

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.description
