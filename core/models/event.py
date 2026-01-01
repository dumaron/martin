from datetime import date, datetime

from django.db import models


class Event(models.Model):
	id = models.AutoField(primary_key=True)
	content = models.TextField()
	date = models.DateField(default=date.today)
	time = models.TimeField(null=True, blank=True, default=datetime.now)
	created_at = models.DateTimeField(auto_now_add=True)
	documents = models.ManyToManyField('Document', blank=True)

	def __str__(self):
		return self.content

	class Meta:
		db_table = 'events'
