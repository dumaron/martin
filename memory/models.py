from django.db import models
from datetime import date, datetime


class Event(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.TextField()
    date = models.DateField(default=date.today)
    time = models.TimeField(null=True, blank=True, default=datetime.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content


class Note(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content
