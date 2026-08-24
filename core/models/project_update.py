from django.db import models

from . import Project


class ProjectUpdate(models.Model):
	id = models.AutoField(primary_key=True)
	content = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.PROTECT, related_name='updates')

	def __str__(self):
		return f'Project "{self.project.title}" update at {self.created_at}'

	class Meta:
		db_table = 'project_updates'
		ordering = ['-created_at']
