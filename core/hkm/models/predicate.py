from django.db import models


class Predicate(models.Model):
	# Predicates are advisory, not enforced: facts reference predicates by plain string, with no foreign key
	# to this table. A predicate can be used on the fly without being declared here; declaring one is an
	# opt-in enrichment that gives it a display label and a semantic value type.

	id = models.CharField(primary_key=True, max_length=128)  # e.g. 'born-in', 'has-child'
	label = models.CharField(max_length=256)  # e.g. 'born in', 'has child' (for display)

	# `value_type` is a semantic tag describing what the fact's object means, not a database type.
	# 'reference' marks the object as an entity identifier (what makes the data a graph); other values are
	# open-ended ('text', 'year', 'date', 'url', ...). Undeclared predicates default to plain text.
	VALUE_TYPE_REFERENCE = 'reference'
	value_type = models.CharField(max_length=32)

	class Meta:
		db_table = 'hkm_predicates'

	def __str__(self):
		return self.id
