from django.test import TestCase
from django.utils import timezone

from core import hkm
from core.hkm.models import Fact
from core.models import Flashcard, FlashcardGenerator
from core.mutations import sync_generated_flashcards


def _apply(facts=(), retractions=()):
	hkm.apply_transaction(hkm.create_draft_transaction(facts, retractions=retractions))


def _retract(subject, predicate, object_):
	_apply(retractions=[Fact.objects.get(subject=subject, predicate=predicate, object=object_).id])


def _active_cards():
	return list(
		Flashcard.objects.filter(archived_at=None).order_by('question').values_list('question', 'answer')
	)


class SyncGeneratedFlashcardsTest(TestCase):
	def setUp(self):
		self.generator = FlashcardGenerator.objects.create(
			name='Authors',
			query='$p, name, $name\n$p, ?wrote, $b',
			question_template='Who wrote $b?',
			answer_template='$name',
		)
		_apply(
			[
				('lem', 'name', 'Stanisław Lem'),
				('lem', 'wrote', 'Solaris'),
				('calvino', 'name', 'Italo Calvino'),
			]
		)

	def test_creates_a_card_for_each_result_with_a_value_for_every_template_variable(self):
		"""
		Lem wrote Solaris, so his row fills both templates and becomes a card, linked to its generator and
		stamped with the sync time. Calvino wrote nothing: his $b is empty, and a card with a hole in it is
		not made.
		"""
		now = timezone.now()

		sync_generated_flashcards(now=now)

		self.assertEqual(_active_cards(), [('Who wrote Solaris?', 'Stanisław Lem')])
		card = Flashcard.objects.get()
		self.assertEqual(card.generator, self.generator)
		self.assertEqual(card.generated_at, now)

	def test_skips_cards_already_present(self):
		"""
		A card with the same question and answer already exists, made by hand, so no generated copy is added,
		not even when the sync runs a second time.
		"""
		Flashcard.objects.create(question='Who wrote Solaris?', answer='Stanisław Lem')

		sync_generated_flashcards()
		sync_generated_flashcards()

		self.assertIsNone(Flashcard.objects.get().generated_at)

	def test_archives_cards_no_generator_produces_any_more(self):
		"""
		Once the fact behind a card is retracted, no generator produces the card any more, so the next sync
		archives it instead of deleting it.
		"""
		sync_generated_flashcards()
		_retract('lem', 'wrote', 'Solaris')

		sync_generated_flashcards()

		self.assertEqual(_active_cards(), [])
		self.assertIsNotNone(Flashcard.objects.get().archived_at)

	def test_brings_back_an_archived_card_produced_again(self):
		"""
		A fact retracted and then asserted again brings back the very card it had, with its review history,
		instead of creating a new one.
		"""
		sync_generated_flashcards()
		card = Flashcard.objects.get()
		_retract('lem', 'wrote', 'Solaris')
		sync_generated_flashcards()
		_apply([('lem', 'wrote', 'Solaris')])

		sync_generated_flashcards()

		card.refresh_from_db()
		self.assertIsNone(card.archived_at)
		self.assertEqual(Flashcard.objects.count(), 1)

	def test_never_archives_cards_made_by_hand(self):
		"""
		A card made by hand is never archived, even though no generator produces it.
		"""
		Flashcard.objects.create(question='Who wrote Ficciones?', answer='Jorge Luis Borges')

		sync_generated_flashcards()

		self.assertIn(('Who wrote Ficciones?', 'Jorge Luis Borges'), _active_cards())
