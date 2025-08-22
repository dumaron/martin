from datetime import timedelta

from django.db import models
from django.utils import timezone

from core.tasks import complete_time_box


class TimeBox(models.Model):
	id = models.AutoField(primary_key=True)
	started_on = models.DateTimeField(null=True, blank=True)
	ended_on = models.DateTimeField(null=True, blank=True)
	has_been_interrupted = models.BooleanField(default=False, null=True, blank=True)
	max_duration_minutes = models.IntegerField()


	def start(self):
		"""
		Starts the TimeBox, ensuring any active TimeBox is interrupted, and schedules its
		completion after the configured maximum duration.

		"""


		# TBH I'm not sure about how the flow is structured. Every timebox that is generated should be also automatically
		# started, but I don't want to override the init method to make things more decoupled. Maybe I'll change it later.


		# We interrupt any existing active TimeBox, even though there should be none.
		# I don't expect to be in this state anytime, but better safe than sorry.
		# Maybe in the future I can spawn some sort of log or, even better, a notification directly in the UI.
		active_time_boxes = TimeBox.objects.filter(ended_on__isnull=True).exclude(id=self.id)

		for active_box in active_time_boxes:
			active_box.interrupt()
		
		self.started_on = timezone.now()
		self.save()
		
		# Schedule completion task
		eta = self.started_on + timedelta(minutes=self.max_duration_minutes)
		complete_time_box.enqueue(self.id, eta=eta)

	def interrupt(self):
		"""
		Interrupts the TimeBox, ensuring it is marked as ended and has_been_interrupted is set to True.
		"""

		# Also this is interesting. Shall I log it somehow?
		if self.ended_on is None:
			self.ended_on = timezone.now()
			self.has_been_interrupted = True
			self.save()
			
			# django-tasks doesn't have a direct way to cancel by eta,
			# so we rely on the task checking if the TimeBox is already ended


	@staticmethod
	def get_active_time_box() -> 'TimeBox | None':
		return TimeBox.objects.filter(ended_on__isnull=True).first()

	def __str__(self):
		return str(self.started_on)

	class Meta:
		db_table = 'time_boxes'
