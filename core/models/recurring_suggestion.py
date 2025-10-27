import recurrence.fields
from django.db import models


class RecurringSuggestion(models.Model):
	id = models.AutoField(primary_key=True)
	content = models.CharField(max_length=1024)
	created_at = models.DateTimeField(auto_now_add=True)
	recurrences = recurrence.fields.RecurrenceField()
	start_date = models.DateField()
	end_date = models.DateField(null=True, blank=True)

	def __str__(self):
		return self.content

	class Meta:
		db_table = 'recurring_suggestions'
