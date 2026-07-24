from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.flashcard_create.flashcard_create import FlashcardForm
from apps.website.pages.page import Page
from core.models import Flashcard

page = Page(name='flashcard_edit_page', base_route='models/flashcard/<int:flashcard_id>')


@page.main
def main_render(request, flashcard_id):
	flashcard = get_object_or_404(Flashcard, pk=flashcard_id)
	form = FlashcardForm(instance=flashcard)
	return render(request, 'flashcard_edit/flashcard_edit.html', {'flashcard': flashcard, 'form': form})


@page.action('update')
def update_flashcard(request, flashcard_id):
	flashcard = get_object_or_404(Flashcard, pk=flashcard_id)
	form = FlashcardForm(request.POST, instance=flashcard)
	if form.is_valid():
		form.save()
		return redirect('flashcard_list_page.main_render')
	else:
		return render(request, 'flashcard_edit/flashcard_edit.html', {'flashcard': flashcard, 'form': form})


@page.action('delete')
def delete_flashcard(request, flashcard_id):
	flashcard = get_object_or_404(Flashcard, pk=flashcard_id)
	flashcard.delete()
	return redirect('flashcard_list_page.main_render')
