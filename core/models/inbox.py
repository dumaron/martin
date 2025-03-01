from django.db import models


class Inbox(models.Model):
    class Contexts(models.TextChoices):
        PRIVATE = 'private'
        WORK = 'work'

    class Meta:
        db_table = 'inboxes'
        verbose_name_plural = 'inboxes'

    id = models.AutoField(primary_key=True)
    content = models.TextField()
    context = models.TextField(choices=Contexts, default=Contexts.PRIVATE)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    # But, does it really make sense to have a "deleted" inbox? What is the difference between a deleted box and
    # a processed one with no consequences?
    # I strongly suspect this attribute will be deleted, but let's see after some actual usage.
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.content