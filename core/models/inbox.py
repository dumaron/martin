from django.db import models


class Inbox(models.Model):
	id = models.AutoField(primary_key=True)
	content = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	processed = models.BooleanField(default=False)
	processed_at = models.DateTimeField(null=True, blank=True)
	
	# GTD processing fields
	created_project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='source_inboxes')
	created_task = models.ForeignKey('Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='source_inboxes')

	def __str__(self):
		status = '✓' if self.processed else '◯'
		return f'{status} {self.content[:50]}...' if len(self.content) > 50 else f'{status} {self.content}'

	class Meta:
		db_table = 'inboxes'
		ordering = ['processed', 'created_at']
