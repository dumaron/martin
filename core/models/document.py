from django.db import models


class Document(models.Model):
	name = models.CharField(max_length=256)
	description = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'documents'