from django.test import TestCase
from django.utils import timezone

from core import hkm
from core.hkm.models import Fact, Retraction, Transaction
from core.utils.fp import lmap


def _staged_triples(transaction):
	return lmap(lambda fact: (fact.subject, fact.predicate, fact.object), transaction.facts.order_by('id'))


def _staged_retraction_ids(transaction):
	return list(transaction.retractions.values_list('fact_id', flat=True))


class CreateDraftTest(TestCase):
	def test_creates_an_unapplied_transaction_with_facts_and_retractions(self):
		"""Creating a draft stores an unapplied transaction with its description, staged facts and staged retractions."""
		applied = Transaction.objects.create(applied_at=timezone.now())
		current = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=applied
		)

		draft = hkm.create_draft_transaction(
			[('rome', 'is-capital-of', 'italy')], retractions=[current.id], description='fix capital'
		)

		self.assertIsNone(draft.applied_at)
		self.assertEqual(draft.description, 'fix capital')
		self.assertEqual(_staged_triples(draft), [('rome', 'is-capital-of', 'italy')])
		self.assertEqual(_staged_retraction_ids(draft), [current.id])


class ApplyTransactionTest(TestCase):
	def test_stamps_applied_at(self):
		"""Applying a draft sets its applied date."""
		draft = hkm.create_draft_transaction([('hannibal', 'crossed', 'alps')])

		hkm.apply_transaction(draft)

		draft.refresh_from_db()
		self.assertIsNotNone(draft.applied_at)

	def test_reapplying_keeps_the_original_timestamp(self):
		"""Applying a transaction that is already applied keeps its first applied date."""
		draft = hkm.create_draft_transaction([('hannibal', 'crossed', 'alps')])
		hkm.apply_transaction(draft)
		first_applied_at = draft.applied_at

		hkm.apply_transaction(draft)

		draft.refresh_from_db()
		self.assertEqual(draft.applied_at, first_applied_at)


class DiscardDraftTest(TestCase):
	def test_deletes_the_draft_and_its_staged_facts_and_retractions(self):
		"""Discarding a draft deletes it with its staged facts and retractions, and leaves the current facts alone."""
		applied = Transaction.objects.create(applied_at=timezone.now())
		current = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=applied
		)
		draft = hkm.create_draft_transaction([('rome', 'is-capital-of', 'italy')], retractions=[current.id])

		hkm.discard_draft(draft)

		self.assertFalse(Transaction.objects.filter(applied_at=None).exists())
		self.assertEqual(list(Fact.objects.all()), [current])
		self.assertFalse(Retraction.objects.exists())

	def test_refuses_to_discard_an_applied_transaction(self):
		"""Discarding an applied transaction raises ValueError."""
		draft = hkm.create_draft_transaction([('hannibal', 'crossed', 'alps')])
		hkm.apply_transaction(draft)

		with self.assertRaises(ValueError):
			hkm.discard_draft(draft)


class UpdateDraftTest(TestCase):
	def setUp(self):
		self.applied = Transaction.objects.create(applied_at=timezone.now())
		self.current = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=self.applied
		)

	def test_replaces_staged_facts_and_description(self):
		"""Updating a draft replaces its staged facts and its description, and the draft stays unapplied."""
		draft = hkm.create_draft_transaction([('michelangelo', 'born-in', 'florencee')], description='old note')

		hkm.update_draft(draft, [('michelangelo', 'born-in', 'florence')], description='fixed note')

		draft.refresh_from_db()
		self.assertEqual(_staged_triples(draft), [('michelangelo', 'born-in', 'florence')])
		self.assertEqual(draft.description, 'fixed note')
		self.assertIsNone(draft.applied_at)

	def test_keeps_the_same_transaction(self):
		"""Updating a draft returns the same transaction and creates no new one."""
		draft = hkm.create_draft_transaction([('michelangelo', 'born-in', 'florencee')])

		updated = hkm.update_draft(draft, [('michelangelo', 'born-in', 'florence')])

		self.assertEqual(updated.id, draft.id)
		# Only the applied transaction from setUp plus this same draft — no extra transaction created.
		self.assertEqual(Transaction.objects.count(), 2)

	def test_can_keep_a_retraction_staged_on_the_same_fact(self):
		"""Updating a draft can stage again the retraction it already had on the same fact."""
		# Re-staging the same retraction must not collide with the OneToOne row left by the previous version.
		draft = hkm.create_draft_transaction([], retractions=[self.current.id])

		hkm.update_draft(draft, [('rome', 'is-capital-of', 'italy')], retractions=[self.current.id])

		self.assertEqual(_staged_retraction_ids(draft), [self.current.id])

	def test_can_drop_a_staged_retraction(self):
		"""Updating a draft without a retraction it had staged removes that retraction."""
		draft = hkm.create_draft_transaction([('rome', 'is-capital-of', 'italy')], retractions=[self.current.id])

		hkm.update_draft(draft, [('rome', 'is-capital-of', 'italy')], retractions=[])

		self.assertFalse(draft.retractions.exists())

	def test_refuses_to_update_an_applied_transaction(self):
		"""Updating an applied transaction raises ValueError and leaves its facts as they were."""
		draft = hkm.create_draft_transaction([('hannibal', 'crossed', 'alps')])
		hkm.apply_transaction(draft)

		with self.assertRaises(ValueError):
			hkm.update_draft(draft, [('hannibal', 'crossed', 'the alps')])

		self.assertEqual(_staged_triples(draft), [('hannibal', 'crossed', 'alps')])
