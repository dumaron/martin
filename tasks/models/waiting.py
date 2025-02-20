from django.db import models
from .project import Project


class Waiting(models.Model):
    class Statuses(models.TextChoices):
        WAITING = 'waiting'
        DONE = 'done'
        DELETED = 'deleted'

    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    content = models.TextField()
    status = models.CharField(max_length=16, choices=Statuses, default=Statuses.WAITING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content