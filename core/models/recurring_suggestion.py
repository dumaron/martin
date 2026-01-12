from django.db import models

from core.models.recurrence_rule import RecurrenceRule


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
		active_rules = RecurrenceRule.get_active_in_date(date)
		active_suggestion_ids = active_rules.values_list('suggestion_id', flat=True)
		return cls.objects.filter(id__in=active_suggestion_ids).all()
