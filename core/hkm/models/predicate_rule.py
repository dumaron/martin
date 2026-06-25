from django.db import models


class PredicateRule(models.Model):
	# A single-step inference rule. Any current fact whose predicate equals `source_predicate` implies a
	# second fact with `implied_predicate`. If `flip` is set, subject and object are swapped in the implied
	# fact (the edge points the other way); otherwise they are kept. This covers the three cheap, one-fact-in
	# one-fact-out axioms:
	#
	#   inverse:      is-father-of -> is-child-of,   flip=True   (the reverse edge)
	#   symmetric:    is-married-to -> is-married-to, flip=True   (inverse onto the same predicate)
	#   subproperty:  is-father-of -> is-parent-of,  flip=False  (same direction, more general)
	#
	# Transitive predicates and property chains (which need a join of two facts and a fixpoint) are
	# deliberately out of scope: a rule here fires exactly once, off asserted facts.
	#
	# Predicates are stored as plain strings with no foreign key, consistent with how `Fact` stores them —
	# a rule can reference a predicate that has no row in `hkm_predicates`.
	source_predicate = models.CharField(max_length=128, db_index=True)
	implied_predicate = models.CharField(max_length=128)
	flip = models.BooleanField(default=False)

	class Meta:
		db_table = 'hkm_predicate_rules'
		constraints = [
			models.UniqueConstraint(
				fields=['source_predicate', 'implied_predicate', 'flip'], name='unique_predicate_rule'
			)
		]

	def __str__(self):
		direction = ' (flipped)' if self.flip else ''
		return f'{self.source_predicate} -> {self.implied_predicate}{direction}'
