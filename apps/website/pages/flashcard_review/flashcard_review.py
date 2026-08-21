from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.website.pages.page import Page
from core.models import Flashcard, FlashcardReview
from core.mutations import review_flashcard

page = Page(name='flashcard_review_page', base_route='knowledge/flashcards/study')


@page.main
def main_render(request):
	now = timezone.now()

	flashcard = Flashcard.due_now(now=now).first()

	if flashcard:
		context = {'flashcard': flashcard, 'due_count': Flashcard.due_now(now=now).count()}
	else:
		# This will have to be fixed in the future. The mental model of my approach should be to do one review session
		# a day, so if we reach this branch we should probably forbid user from doing more reviews later today, and tell
		# him/her to come back tomorrow instead.
		# That will likely require a new entity, something like `ReviewSession` or `StudySession`. Out of scope for now.
		context = {
			'flashcard': None,
			'next_due': Flashcard.next_due_at(now=now),
			'reviewed_today': FlashcardReview.objects.filter(reviewed_at__date=now.date()).count(),
		}

	return render(request, 'flashcard_review/flashcard_review.html', context)


@page.action('answer')
def answer_flashcard(request):
	flashcard = get_object_or_404(Flashcard, pk=request.POST.get('flashcard_id'))
	rating = request.POST.get('rating')

	if rating not in ('1', '2', '3', '4'):
		return HttpResponseBadRequest('Invalid flashcard rating')

	review_flashcard(flashcard, int(rating))

	return redirect('flashcard_review_page.main_render')
