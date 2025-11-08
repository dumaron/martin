from django.db import models


class RecurringSuggestion(models.Model):
	id = models.AutoField(primary_key=True)
	content = models.CharField(max_length=1024)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.content

	class Meta:
		db_table = 'recurring_suggestions'


	@classmethod
	def get_actives_in_date(cls, date):
		return cls.objects.filter(start_date__lte=date, end_date__gte=date)
