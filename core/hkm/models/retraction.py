from django.db import models

from core.hkm.models.fact import Fact
from core.hkm.models.transaction import Transaction


class Retraction(models.Model):
	# Append-only correction: a fact is never deleted, it gets retracted by id. Using the fact as primary
	# key enforces "a fact is retracted at most once". There is no un-retract — reviving a fact means
	# re-asserting it as a new fact.

	fact = models.OneToOneField(Fact, primary_key=True, on_delete=models.PROTECT, related_name='retraction')
	reason = models.TextField(blank=True, null=True)
	transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='retractions')

	class Meta:
		db_table = 'hkm_retractions'

	def __str__(self):
		return f'Retraction of fact {self.fact_id}'
