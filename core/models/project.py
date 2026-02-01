from django.db import models

from utils.failures import Failure


class Project(models.Model):
	max_global_active_number = 10

	STATUS_CHOICES = [
		('active', 'Active'),
		('pending', 'Pending'),
		('suspended', 'Suspended'),
		('archived', 'Archived'),
		('completed', 'Completed'),
		('aborted', 'Aborted'),
	]

	id = models.AutoField(primary_key=True)
	title = models.CharField(max_length=255)
	goal = models.TextField(blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

	def __str__(self):
		return f'{self.title} ({self.get_status_display()})'

	def get_children(self):
		return Project.objects.filter(parent=self, status='active')

	def promote_to_active(self):
		currently_active_number = Project.objects.filter(status='active').count()
		if currently_active_number > Project.max_global_active_number:
			return Failure(f'Cannot create more than {Project.max_global_active_number} active projects')
		self.status = 'active'
		self.save()
		return self

	class Meta:
		db_table = 'projects'
		ordering = ['-created_at']
