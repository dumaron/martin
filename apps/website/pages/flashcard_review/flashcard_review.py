from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from apps.website.pages.page import Page
from core.models import Flashcard, FlashcardReview
from core.mutations import review_flashcard

page = Page(name='flashcard_review_page', base_route='srs/review')


@page.main
def main_render(request):
	tag = request.GET.get('tag') or None
	now = timezone.now()

	flashcard = Flashcard.due_now(now=now, tag=tag).first()
	context = {'flashcard': flashcard, 'tag': tag}

	if flashcard:
		context['due_count'] = Flashcard.due_now(now=now, tag=tag).count()
	else:
		# Session done. Learning cards may be due again in minutes: surface the next due time.
		upcoming = Flashcard.objects.filter(due__gt=now).order_by('due')
		if tag:
			upcoming = upcoming.filter(tags__name=tag)

		next_card = upcoming.first()
		context['next_due'] = next_card.due if next_card else None
		context['reviewed_today'] = FlashcardReview.objects.filter(reviewed_at__date=now.date()).count()

	return render(request, 'flashcard_review/flashcard_review.html', context)


@page.action('answer')
def answer_flashcard(request):
	flashcard = get_object_or_404(Flashcard, pk=request.POST.get('flashcard_id'))
	rating = int(request.POST.get('rating'))

	if rating in (1, 2, 3, 4):
		review_flashcard(flashcard, rating)

	url = reverse('flashcard_review_page.main_render')
	tag = request.POST.get('tag')
	return redirect(f'{url}?{urlencode({"tag": tag})}' if tag else url)
