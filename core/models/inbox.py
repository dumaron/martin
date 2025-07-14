from django.db import models


class Inbox(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return self.content

    class Meta:
        db_table = 'inboxes'