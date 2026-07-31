from django.db import models


class InferredFact(models.Model):
	# Read-only window on the `hkm_inferred_facts` SQL view (defined in core/hkm/views_sql.py): the current
	# facts plus the edges the predicate rules imply, collapsed to one row per distinct triple. Unmanaged for
	# the same reasons as CurrentFact — see the comment there.

	# Positional, assigned by a ROW_NUMBER in the view: the triple is the real identity, but Django insists on
	# a primary key. It renumbers whenever the graph changes, so never store it.
	id = models.IntegerField(primary_key=True)
	subject = models.CharField(max_length=512)
	predicate = models.CharField(max_length=128)
	object = models.TextField()
	# 'asserted' when the triple is stated by a fact, 'implied' when only a predicate rule produces it.
	origin = models.CharField(max_length=16)
	# The fact the edge comes from, so an implied one can be traced back. Deliberately not a ForeignKey: for a
	# triple that several facts produce it is whichever the view picked, not a relation worth following.
	source_fact_id = models.IntegerField()

	class Meta:
		managed = False
		db_table = 'hkm_inferred_facts'

	def __str__(self):
		return f'({self.subject}, {self.predicate}, {self.object}) [{self.origin}]'
