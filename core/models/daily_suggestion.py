from django.db import models


class DailySuggestion(models.Model):
	date = models.DateField(primary_key=True)
	content = models.TextField(null=True, blank=True)

	@staticmethod
	def get_or_create(date):
		try:
			return DailySuggestion.objects.get(date=date)
		except DailySuggestion.DoesNotExist:
			return DailySuggestion.objects.create(date=date)

	def __str__(self):
		return f"Daily suggestions {self.date}"