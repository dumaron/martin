from django.db import models
from django.utils import timezone


class Inbox(models.Model):
	id = models.AutoField(primary_key=True)
	content = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	processed_at = models.DateTimeField(null=True, blank=True)

	@property
	def processed(self):
		return self.processed_at is not None

	def __str__(self):
		status = '✓' if self.processed else '◯'
		return f'{status} {self.content[:50]}'

	class Meta:
		db_table = 'inboxes'
		ordering = ['created_at']

	def created_days_ago(self):
		return (timezone.now() - self.created_at).days
