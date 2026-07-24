from django.db import models


class FlashcardReview(models.Model):
	# Integer values mirror fsrs.Rating exactly
	class Rating(models.IntegerChoices):
		AGAIN = 1
		HARD = 2
		GOOD = 3
		EASY = 4

	flashcard = models.ForeignKey('core.Flashcard', on_delete=models.CASCADE, related_name='reviews')
	rating = models.IntegerField(choices=Rating.choices)
	reviewed_at = models.DateTimeField(db_index=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'flashcard_reviews'

	def __str__(self):
		return f'{self.get_rating_display()} on flashcard {self.flashcard_id} at {self.reviewed_at:%Y-%m-%d %H:%M}'
