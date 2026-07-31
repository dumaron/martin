from django.db import models


class CurrentFact(models.Model):
	# Read-only window on the `hkm_current_facts` SQL view (defined in core/hkm/views_sql.py): the asserted
	# facts that are live right now — from an applied transaction, and not removed by an applied retraction.
	# Anything a draft asserts or retracts is absent, having no effect until that draft is applied.
	#
	# `managed = False` because there is nothing to create or alter: the view is built by migration 0027 and by
	# the post_migrate hook in core/apps.py. It also keeps the test runner from trying to build a table for it.
	# The fields are read-only by nature — writes go through Fact and Retraction.

	# The id of the underlying fact, which is what a Retraction points at.
	id = models.IntegerField(primary_key=True)
	subject = models.CharField(max_length=512)
	predicate = models.CharField(max_length=128)
	object = models.TextField()

	class Meta:
		managed = False
		db_table = 'hkm_current_facts'

	def __str__(self):
		return f'({self.subject}, {self.predicate}, {self.object})'
