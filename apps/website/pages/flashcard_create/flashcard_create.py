from django import forms
from django.shortcuts import redirect, render

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


page = Page(name='flashcard_create_page', base_route='models/flashcard/create')


@page.main
def main_render(request):
	form = FlashcardForm()
	return render(request, 'flashcard_create/flashcard_create.html', {'form': form})


@page.action('create-action')
def create_flashcard(request):
	form = FlashcardForm(request.POST)
	if form.is_valid():
		form.save()
		return redirect('flashcard_list_page.main_render')
	else:
		return render(request, 'flashcard_create/flashcard_create.html', {'form': form})
