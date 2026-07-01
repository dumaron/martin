from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core import hkm
from core.hkm.models import Fact, Retraction, Transaction


class RetractionConstraintTest(TestCase):
	def setUp(self):
		self.applied_tx = Transaction.objects.create(applied_at=timezone.now())

	def test_fact_can_be_retracted_at_most_once(self):
		fact = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=self.applied_tx
		)
		Retraction.objects.create(fact=fact, transaction=self.applied_tx)

		with self.assertRaises(IntegrityError):
			Retraction.objects.create(fact=fact, reason='again', transaction=self.applied_tx)


class EntitiesTest(TestCase):
	def setUp(self):
		self.tx = Transaction.objects.create(applied_at=timezone.now())

	def test_lists_distinct_subjects_sorted(self):
		Fact.objects.create(subject='michelangelo', predicate='born-in', object='florence', transaction=self.tx)
		Fact.objects.create(subject='michelangelo', predicate='born-in-year', object='1475', transaction=self.tx)
		Fact.objects.create(subject='hannibal', predicate='crossed', object='alps', transaction=self.tx)

		self.assertEqual(list(hkm.get_all_entities()), ['hannibal', 'michelangelo'])

	def test_ignores_subjects_known_only_through_non_current_facts(self):
		draft_tx = Transaction.objects.create()
		Fact.objects.create(subject='draft-only', predicate='label', object='Draft', transaction=draft_tx)
		retracted = Fact.objects.create(
			subject='retracted-only', predicate='label', object='Gone', transaction=self.tx
		)
		Retraction.objects.create(fact=retracted, transaction=self.tx)

		self.assertEqual(list(hkm.get_all_entities()), [])


class FactsTest(TestCase):
	def setUp(self):
		self.tx = Transaction.objects.create(applied_at=timezone.now())

	def test_returns_current_facts_for_the_subject(self):
		Fact.objects.create(subject='michelangelo', predicate='born-in', object='florence', transaction=self.tx)
		Fact.objects.create(subject='michelangelo', predicate='born-in-year', object='1475', transaction=self.tx)

		triples = [(f['subject'], f['predicate'], f['object']) for f in hkm.get_facts('michelangelo')]
		self.assertCountEqual(
			triples, [('michelangelo', 'born-in', 'florence'), ('michelangelo', 'born-in-year', '1475')]
		)

	def test_excludes_facts_about_other_subjects(self):
		Fact.objects.create(subject='hannibal', predicate='crossed', object='alps', transaction=self.tx)

		self.assertEqual(list(hkm.get_facts('michelangelo')), [])

	def test_excludes_non_current_facts(self):
		draft_tx = Transaction.objects.create()
		Fact.objects.create(subject='rome', predicate='founded-in', object='-753', transaction=draft_tx)
		retracted = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=self.tx
		)
		Retraction.objects.create(fact=retracted, transaction=self.tx)

		self.assertEqual(list(hkm.get_facts('rome')), [])
