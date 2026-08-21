from datetime import datetime

from django.db import transaction as db_transaction
from django.utils import timezone
from fsrs import Card as FsrsCard
from fsrs import Rating, Scheduler
from fsrs import State as FsrsState

from core.models import Flashcard, FlashcardReview

# Default FSRS parameters: desired_retention=0.9, learning_steps=(1m, 10m), relearning_steps=(10m,),
# maximum_interval=36500 days, fuzzing enabled.
scheduler = Scheduler()


def review_flashcard(
	flashcard: Flashcard, rating: int, reviewed_at: datetime | None = None
) -> FlashcardReview:
	"""
	Applies an FSRS review to a flashcard: reschedules it and persists a review log row.

	`reviewed_at` is injectable so tests don't need to mock time.
	"""
	reviewed_at = reviewed_at or timezone.now()

	with db_transaction.atomic():
		fsrs_card = FsrsCard(
			card_id=flashcard.id,
			state=FsrsState(flashcard.state),
			step=flashcard.step,
			stability=flashcard.stability,
			difficulty=flashcard.difficulty,
			due=flashcard.due,
			last_review=flashcard.last_review,
		)
		updated_card, _ = scheduler.review_card(fsrs_card, Rating(rating), review_datetime=reviewed_at)

		flashcard.state = updated_card.state.value
		flashcard.step = updated_card.step
		flashcard.stability = updated_card.stability
		flashcard.difficulty = updated_card.difficulty
		flashcard.due = updated_card.due
		flashcard.last_review = updated_card.last_review
		flashcard.save()

		return FlashcardReview.objects.create(flashcard=flashcard, rating=rating, reviewed_at=reviewed_at)
