from django.db import models
from datetime import date


class Project(models.Model):

    class Statuses(models.TextChoices):
        ACTIVE = 'active'
        ARCHIVED = 'archived'
        DELETED = 'deleted'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=1024)
    parent_project = models.ForeignKey('Project', on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(choices=Statuses, max_length=32)

    def __str__(self):
        return self.name


class Todo(models.Model):

    class Statuses(models.TextChoices):
        TODO = 'todo'
        ACTIVE = 'active'
        DONE = 'done'
        ARCHIVED = 'archived'
        DELETED = 'deleted'

    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=2048)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(choices=Statuses, max_length=32)
    valid_from = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    priority = models.SmallIntegerField(default=0)
    daily_priority_increase = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_valid_order_pray = models.BooleanField(default=False)
    inbox_after_completion = models.TextField(null=True, blank=True)
    last_increase = models.DateField(default=date.today)
    snoozed_until = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if (self.status == Todo.Statuses.DONE or self.status == Todo.Statuses.ACTIVE) and self.inbox_after_completion is not None:
            current_todo = Todo.objects.get(pk=self.id)
            if current_todo.status == Todo.Statuses.TODO:
                # Then I know the model has changed from "to do" to "done", and it needs to spawn the inbox
                inbox = Inbox(content=self.inbox_after_completion)
                inbox.save()

        return super().save(*args, **kwargs)


    def __str__(self):
        return self.description


class Inbox(models.Model):

    class Contexts(models.TextChoices):
        PRIVATE = 'private'
        WORK = 'work'

    class Meta:
        verbose_name_plural = 'inboxes'

    id = models.AutoField(primary_key=True)
    content = models.TextField()
    context = models.TextField(choices=Contexts, default=Contexts.PRIVATE)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.content


class Update(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Update for project {self.project} on {self.created_at}'
