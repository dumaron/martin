from django.db import models

from core.hkm.models.transaction import Transaction


class FactQuerySet(models.QuerySet):
	def current(self):
		# The `current_facts` view of the reference schema: current knowledge is facts that have not been
		# retracted. On top of that, since we implement the draft lifecycle, facts only count once their
		# transaction has been applied — an unapplied transaction is an uncommitted draft.
		return self.filter(retraction__isnull=True, transaction__applied_at__isnull=False)


class Fact(models.Model):
	# The atom of the knowledge base: an append-only (subject, predicate, object) triple. Facts are never
	# updated or deleted — corrections happen by inserting a Retraction and asserting a new fact.
	#
	# There is deliberately no foreign key on `subject`, `object`, or `predicate`: entities exist simply by
	# being mentioned (no registration step), and predicates work without a row in `hkm_predicates`. The
	# resulting soft spots (typos creating phantom entities, etc.) are handled at the application layer,
	# not by the schema — don't add constraints here "for safety".

	subject = models.CharField(max_length=512, db_index=True)  # entity id, or 'f:<id>' to annotate a fact
	predicate = models.CharField(max_length=128, db_index=True)  # advisory match against Predicate.id
	object = models.TextField(
		db_index=True
	)  # entity id if the predicate's value_type is 'reference', else a scalar
	transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='facts')

	objects = FactQuerySet.as_manager()

	class Meta:
		db_table = 'hkm_facts'

	def __str__(self):
		return f'({self.subject}, {self.predicate}, {self.object})'
