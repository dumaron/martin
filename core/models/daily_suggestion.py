from django.db import models


class DailySuggestion(models.Model):
	date = models.DateField(primary_key=True)
	content = models.TextField(null=True, blank=True)

	def __str__(self):
		return f'Daily suggestions for {self.date}'

	class Meta:
		db_table = 'daily_suggestions'
