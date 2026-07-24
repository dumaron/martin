from django.db import models
from django.db.models import Q
from django.utils import timezone
from taggit.managers import TaggableManager


class Flashcard(models.Model):
	# Integer values mirror fsrs.State exactly
	class State(models.IntegerChoices):
		LEARNING = 1
		REVIEW = 2
		RELEARNING = 3

	question = models.TextField()
	answer = models.TextField()
	tags = TaggableManager(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	# FSRS scheduling state, a column-per-field mirror of fsrs.Card.
	# The defaults reproduce a brand-new fsrs.Card(): Learning state, step 0, no stability/difficulty
	# yet, due immediately, never reviewed. `step` is None once the card graduates to Review state.
	state = models.IntegerField(choices=State.choices, default=State.LEARNING)
	step = models.IntegerField(blank=True, null=True, default=0)
	stability = models.FloatField(blank=True, null=True)
	difficulty = models.FloatField(blank=True, null=True)
	due = models.DateTimeField(default=timezone.now, db_index=True)
	last_review = models.DateTimeField(blank=True, null=True)

	class Meta:
		db_table = 'flashcards'

	def __str__(self):
		return self.question

	@staticmethod
	def due_now(now=None, tag=None) -> 'models.QuerySet[Flashcard]':
		"""
		Cards reviewable right now, most overdue first.

		Learning/relearning cards have minute-scale due times and must respect them exactly: that is
		what makes a failed card reappear within the same review session. Review cards get
		datetime-precise due dates from FSRS, but Anki-style we treat them with day granularity: a
		review card due at 22:00 today is already reviewable this morning.
		"""
		now = now or timezone.now()
		queryset = Flashcard.objects.filter(
			Q(due__lte=now) | Q(state=Flashcard.State.REVIEW, due__date__lte=now.date())
		)

		if tag:
			queryset = queryset.filter(tags__name=tag)

		return queryset.order_by('due', 'id')
