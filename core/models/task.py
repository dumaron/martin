from django.db import models


class Task(models.Model):
	STATUS_CHOICES = [
		('active', 'Active'),
		('completed', 'Completed'),
		('pending', 'Pending'),
		('aborted', 'Aborted'),
	]

	id = models.AutoField(primary_key=True)
	description = models.TextField(blank=True)
	project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	created_at = models.DateTimeField(auto_now_add=True)
	completed_at = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		status = '✓' if self.status == 'completed' else '◯'
		return f'{status} {self.description}'

	class Meta:
		ordering = ['created_at']
