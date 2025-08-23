from django.db import models


class Project(models.Model):
	STATUS_CHOICES = [
		('active', 'Active'),
		('suspended', 'Suspended'),
		('archived', 'Archived'),
		('done', 'Done'),
	]
	
	id = models.AutoField(primary_key=True)
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	def __str__(self):
		return f'{self.title} ({self.get_status_display()})'
	
	class Meta:
		ordering = ['-created_at']