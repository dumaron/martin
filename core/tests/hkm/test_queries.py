from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core import hkm
from core.hkm.models import Fact, Retraction, Transaction
from core.utils.fp import lmap


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


class DraftTransactionsTest(TestCase):
	def test_lists_unapplied_transactions_with_their_staged_counts(self):
		applied = Transaction.objects.create(applied_at=timezone.now())
		current = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=applied
		)
		draft = Transaction.objects.create(description='fix capital')
		Fact.objects.create(subject='rome', predicate='is-capital-of', object='italy', transaction=draft)
		Fact.objects.create(subject='rome', predicate='founded-in', object='-753', transaction=draft)
		Retraction.objects.create(fact=current, transaction=draft)

		drafts = list(hkm.get_draft_transactions())

		self.assertEqual(lmap(lambda d: d.id, drafts), [draft.id])
		self.assertEqual(drafts[0].fact_count, 2)
		self.assertEqual(drafts[0].retraction_count, 1)
		self.assertEqual(drafts[0].description, 'fix capital')

	def test_lists_oldest_first(self):
		older = Transaction.objects.create()
		newer = Transaction.objects.create()

		self.assertEqual(lmap(lambda d: d.id, hkm.get_draft_transactions()), [older.id, newer.id])


class RetractableFactsTest(TestCase):
	def setUp(self):
		self.tx = Transaction.objects.create(applied_at=timezone.now())
		self.fact = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=self.tx
		)

	def _retractable_ids(self, **kwargs):
		return lmap(lambda fact: fact['id'], hkm.get_retractable_facts(**kwargs))

	def test_offers_current_unretracted_facts(self):
		self.assertEqual(self._retractable_ids(), [self.fact.id])

	def test_excludes_facts_with_a_retraction_even_a_draft_one(self):
		draft = Transaction.objects.create()
		Retraction.objects.create(fact=self.fact, transaction=draft)

		self.assertEqual(self._retractable_ids(), [])

	def test_ignores_retractions_staged_by_the_transaction_being_edited(self):
		draft = Transaction.objects.create()
		Retraction.objects.create(fact=self.fact, transaction=draft)

		self.assertEqual(self._retractable_ids(ignore_transaction_id=draft.id), [self.fact.id])

	def test_still_excludes_retractions_staged_by_other_transactions(self):
		other = Transaction.objects.create()
		Retraction.objects.create(fact=self.fact, transaction=other)
		editing = Transaction.objects.create()

		self.assertEqual(self._retractable_ids(ignore_transaction_id=editing.id), [])


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
