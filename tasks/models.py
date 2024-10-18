from random import choices

from django.db import models


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
    is_valid_order_pray =  models.BooleanField(default=False)

    def __str__(self):
        return self.description


class Inbox(models.Model):

    class Contexts(models.TextChoices):
        PRIVATE = 'private'
        WORK = 'work'

    id = models.AutoField(primary_key=True)
    content = models.TextField()
    context = models.TextField(choices=Contexts, default=Contexts.PRIVATE)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)


class Update(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Update for project {self.project} on {self.created_at}'
