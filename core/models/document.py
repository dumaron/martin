from django.db import models
from taggit.managers import TaggableManager


class Document(models.Model):
	name = models.CharField(max_length=256)
	description = models.TextField(blank=True, null=True)
	location = models.CharField(max_length=256, blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	tags = TaggableManager()

	class Meta:
		db_table = 'documents'
