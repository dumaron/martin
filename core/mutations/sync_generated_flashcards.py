from itertools import starmap

from django.db import transaction as db_transaction
from django.utils import timezone

from core.models import Flashcard, FlashcardGenerator
from core.utils.fp import lfilter, lmap, separate


def _text(card):
	return card.question, card.answer


def sync_generated_flashcards(now=None):
	now = now or timezone.now()

	with db_transaction.atomic():
		generators = FlashcardGenerator.objects.order_by('id')
		produced = {text: generator for generator in generators for text in generator.cards()}
		active, archived = separate(lambda card: card.archived_at is None, Flashcard.objects.all())

		stale = lfilter(lambda card: card.generated_at and _text(card) not in produced, active)
		Flashcard.objects.filter(id__in=lmap(lambda card: card.id, stale)).update(archived_at=now)

		present = set(map(_text, active))
		revivable = {_text(card): card for card in archived if card.generated_at}
		revived, new = separate(lambda text: text in revivable, sorted(produced.keys() - present))
		for text in revived:
			Flashcard.objects.filter(id=revivable[text].id).update(archived_at=None, generator=produced[text])
		Flashcard.objects.bulk_create(
			starmap(
				lambda question, answer: Flashcard(
					question=question, answer=answer, generator=produced[question, answer], generated_at=now
				),
				new,
			)
		)
