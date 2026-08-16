from django import forms
from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
from core.models import Flashcard


class FlashcardForm(forms.ModelForm):
	class Meta:
		model = Flashcard
		fields = ['question', 'answer', 'tags']
		widgets = {
			'question': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Question'}),
			'answer': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Answer'}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['tags'].required = False


page = Page(name='flashcard_upsert_page', base_route='knowledge/flashcards')


def _flashcard_or_none(flashcard_id):
	return get_object_or_404(Flashcard, pk=flashcard_id) if flashcard_id else None


@page.main(['new', '<int:flashcard_id>/edit'])
def main_render(request, flashcard_id=None):
	flashcard = _flashcard_or_none(flashcard_id)
	form = FlashcardForm(instance=flashcard)
	return render(request, 'flashcard_upsert/flashcard_upsert.html', {'flashcard': flashcard, 'form': form})


@page.action('<int?:flashcard_id>/save')
def save_flashcard(request, flashcard_id=None):
	flashcard = _flashcard_or_none(flashcard_id)
	form = FlashcardForm(request.POST, instance=flashcard)
	if form.is_valid():
		form.save()
		return redirect('flashcard_list_page.main_render')
	else:
		return render(request, 'flashcard_upsert/flashcard_upsert.html', {'flashcard': flashcard, 'form': form})


@page.action('<int:flashcard_id>/delete')
def delete_flashcard(request, flashcard_id):
	flashcard = get_object_or_404(Flashcard, pk=flashcard_id)
	flashcard.delete()
	return redirect('flashcard_list_page.main_render')
