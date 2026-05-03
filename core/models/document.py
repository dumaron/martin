from django.db import models
from taggit.managers import TaggableManager


class Document(models.Model):
	name = models.CharField(max_length=256)
	description = models.TextField(blank=True, null=True)
	location = models.CharField(max_length=256, blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	# Representative date is a generic field to give temporal context to documents that aren't tied to specific events.
	# --
	# Almost every document is related to an event. However, some of these documents might be old ones I am uploading to
	# Martin for which I no longer remember the related event. Other times, the event is somewhat irrelevant, like
	# receiving an email with a bill, and I don't want to force myself to create an event object for such minor events
	# that will likely create a lot of noise.
	#
	# This date field will help me show these documents in timelines and historical reconstructions, while avoiding the
	# burden of making a new event every time.
	#
	# `representative_date` is probably a catch-all for many concepts that could be related to a document
	# (created_on, received_on, valid_since, etc.) but it should be enough while I try to create a prototype for HKM.

	representative_date = models.DateField(
		blank=True,
		null=True,
		help_text="Optional date that anchors this document in time when it isn't tied to an event.",
	)
	tags = TaggableManager()

	class Meta:
		db_table = 'documents'

	def __str__(self):
		return self.name
