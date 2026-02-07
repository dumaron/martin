from django.db import models

from core.models.project import Project


class Maybe(models.Model):
	STATUS_CHOICES = [('open', 'Open'), ('promoted', 'Promoted'), ('dismissed', 'Dismissed')]

	id = models.AutoField(primary_key=True)
	title = models.CharField(max_length=255)
	notes = models.TextField(blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.title

	def promote_to_project(self):
		project = Project.objects.create(title=self.title, status='active')
		self.status = 'promoted'
		self.save()
		return project

	def dismiss(self):
		self.status = 'dismissed'
		self.save()

	class Meta:
		db_table = 'maybes'
		ordering = ['-created_at']
