from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core.hkm.models import Fact, Retraction, Transaction


class RetractionConstraintTest(TestCase):
	def setUp(self):
		self.applied_tx = Transaction.objects.create(applied_at=timezone.now())

	def test_fact_can_be_retracted_at_most_once(self):
		"""Retracting a fact that already has a retraction raises IntegrityError."""
		fact = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=self.applied_tx
		)
		Retraction.objects.create(fact=fact, transaction=self.applied_tx)

		with self.assertRaises(IntegrityError):
			Retraction.objects.create(fact=fact, reason='again', transaction=self.applied_tx)
