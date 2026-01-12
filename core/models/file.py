from django.db import models


class File(models.Model):
	file = models.FileField()
	uploaded_at = models.DateTimeField(auto_now_add=True)
	document = models.ForeignKey('Document', on_delete=models.CASCADE, null=True, blank=True)

	class Meta:
		db_table = 'files'
