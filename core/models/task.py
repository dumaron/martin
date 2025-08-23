from django.db import models


class Task(models.Model):
	id = models.AutoField(primary_key=True)
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='tasks')
	is_done = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	completed_at = models.DateTimeField(null=True, blank=True)
	
	def __str__(self):
		status = '✓' if self.is_done else '◯'
		return f'{status} {self.title}'
	
	class Meta:
		ordering = ['is_done', '-created_at']