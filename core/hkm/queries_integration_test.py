from django.test import TestCase
from django.utils import timezone

from core import hkm
from core.hkm.models import Fact, Retraction, Transaction
from core.utils.fp import lmap


class EntitiesTest(TestCase):
	def setUp(self):
		self.tx = Transaction.objects.create(applied_at=timezone.now())

	def test_lists_distinct_subjects_sorted(self):
		"""Entities are the distinct subjects of the current facts, in alphabetical order."""
		Fact.objects.create(subject='michelangelo', predicate='born-in', object='florence', transaction=self.tx)
		Fact.objects.create(subject='michelangelo', predicate='born-in-year', object='1475', transaction=self.tx)
		Fact.objects.create(subject='hannibal', predicate='crossed', object='alps', transaction=self.tx)

		self.assertEqual(list(hkm.get_all_entities()), ['hannibal', 'michelangelo'])

	def test_ignores_subjects_known_only_through_non_current_facts(self):
		"""A subject known only through a draft fact or a retracted fact is not an entity."""
		draft_tx = Transaction.objects.create()
		Fact.objects.create(subject='draft-only', predicate='label', object='Draft', transaction=draft_tx)
		retracted = Fact.objects.create(
			subject='retracted-only', predicate='label', object='Gone', transaction=self.tx
		)
		Retraction.objects.create(fact=retracted, transaction=self.tx)

		self.assertEqual(list(hkm.get_all_entities()), [])


class DraftTransactionsTest(TestCase):
	def test_lists_unapplied_transactions_with_their_staged_counts(self):
		"""Only unapplied transactions are listed, each with its description and its counts of staged facts and retractions."""
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
		"""Drafts are listed from the oldest to the newest."""
		older = Transaction.objects.create()
		newer = Transaction.objects.create()

		self.assertEqual(lmap(lambda d: d.id, hkm.get_draft_transactions()), [older.id, newer.id])


class RetractableFactsTest(TestCase):
	def setUp(self):
		self.tx = Transaction.objects.create(applied_at=timezone.now())
		self.fact = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=self.tx
		)

	def _retractable_ids(self):
		return lmap(lambda fact: fact['id'], hkm.get_retractable_facts())

	def test_offers_current_unretracted_facts(self):
		"""A current fact with no retraction is offered for retraction."""
		self.assertEqual(self._retractable_ids(), [self.fact.id])

	def test_keeps_offering_a_fact_a_draft_has_staged_for_retraction(self):
		"""A fact whose retraction is only staged by a draft is still offered."""
		# A staged retraction has removed nothing yet, so the fact is still current — and still on offer, which
		# is what lets the draft that staged it show its own selection back when reopened.
		draft = Transaction.objects.create()
		Retraction.objects.create(fact=self.fact, transaction=draft)

		self.assertEqual(self._retractable_ids(), [self.fact.id])

	def test_excludes_a_fact_an_applied_retraction_has_removed(self):
		"""A fact removed by an applied retraction is no longer offered."""
		Retraction.objects.create(fact=self.fact, transaction=self.tx)

		self.assertEqual(self._retractable_ids(), [])

	def test_excludes_facts_asserted_by_a_draft(self):
		"""A fact asserted only by a draft is not offered."""
		draft = Transaction.objects.create()
		Fact.objects.create(subject='rome', predicate='founded-in', object='-753', transaction=draft)

		self.assertEqual(self._retractable_ids(), [self.fact.id])


class FactsTest(TestCase):
	def setUp(self):
		self.tx = Transaction.objects.create(applied_at=timezone.now())

	def test_returns_current_facts_for_the_subject(self):
		"""All the current facts of the subject are returned."""
		Fact.objects.create(subject='michelangelo', predicate='born-in', object='florence', transaction=self.tx)
		Fact.objects.create(subject='michelangelo', predicate='born-in-year', object='1475', transaction=self.tx)

		triples = lmap(
			lambda fact: (fact['subject'], fact['predicate'], fact['object']), hkm.get_facts('michelangelo')
		)
		self.assertCountEqual(
			triples, [('michelangelo', 'born-in', 'florence'), ('michelangelo', 'born-in-year', '1475')]
		)

	def test_excludes_facts_about_other_subjects(self):
		"""Facts about other subjects are not returned."""
		Fact.objects.create(subject='hannibal', predicate='crossed', object='alps', transaction=self.tx)

		self.assertEqual(list(hkm.get_facts('michelangelo')), [])

	def test_excludes_non_current_facts(self):
		"""Draft facts and retracted facts of the subject are not returned."""
		draft_tx = Transaction.objects.create()
		Fact.objects.create(subject='rome', predicate='founded-in', object='-753', transaction=draft_tx)
		retracted = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=self.tx
		)
		Retraction.objects.create(fact=retracted, transaction=self.tx)

		self.assertEqual(list(hkm.get_facts('rome')), [])
