import random
from datetime import datetime

from django.db import models


class Memory(models.Model):
	id = models.AutoField(primary_key=True)
	created_at = models.DateTimeField(auto_now_add=True)
	photo = models.FileField(upload_to='memories/')
	description = models.TextField(blank=True)
	location = models.CharField(max_length=256, blank=True, null=True)
	date = models.DateField(blank=True, null=True)
	last_selected_on = models.DateField(blank=True, null=True)

	def __str__(self):
		return f'Memory {self.id}'

	class Meta:
		db_table = 'memories'
		verbose_name_plural = 'memories'

	@staticmethod
	def select_memory_for_today():
		"""
		Select a memory to be shown today among the one never selected before or selected a long time ago
		"""

		today = datetime.today().date()

		# If a memory has already been selected for being shown today, we just return it
		already_selected_memory = Memory.objects.filter(last_selected_on=today).first()

		if already_selected_memory:
			return already_selected_memory

		# Otherwise we take the last 10 ordered by selection date, and we randomly return one of them
		last_10_memories = Memory.objects.order_by('last_selected_on')[:10]

		# If there are no memories (weird? empty DB?) raise an exception, this is not supposed to happen
		if not last_10_memories:
			raise Exception('No memories found')  # that error message looks so cool...

		selected_memory = random.choice(last_10_memories)
		selected_memory.last_selected_on = today
		selected_memory.save()

		return selected_memory
