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
