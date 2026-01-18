from django.db import models
from django.utils import timezone


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

	def mark_as_completed(self):
		"""Mark the task as completed with current timestamp."""
		if self.status != 'completed':
			self.status = 'completed'
			self.completed_at = timezone.now()
			self.save()

	def abort(self):
		"""Abort the task and clear completion timestamp."""
		if self.status != 'aborted':
			self.status = 'aborted'
			self.completed_at = None
			self.save()

	class Meta:
		ordering = ['created_at']
