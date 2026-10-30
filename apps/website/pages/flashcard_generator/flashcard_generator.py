from django import forms
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
from core.models import FlashcardGenerator
from core.mutations import sync_generated_flashcards


class FlashcardGeneratorForm(forms.ModelForm):
	class Meta:
		model = FlashcardGenerator
		fields = ['name', 'query', 'question_template', 'answer_template']
		widgets = {
			'query': forms.Textarea(attrs={'rows': 6}),
			'question_template': forms.Textarea(attrs={'rows': 2}),
			'answer_template': forms.Textarea(attrs={'rows': 2}),
		}


page = Page(name='flashcard_generator_page', base_route='knowledge/flashcards/generators')


def _generator_or_none(generator_id):
	return get_object_or_404(FlashcardGenerator, pk=generator_id) if generator_id else None


def _render(request, generator, form):
	generators = FlashcardGenerator.objects.annotate(
		card_count=Count('flashcards', filter=Q(flashcards__archived_at=None))
	).order_by('name')
	context = {'generator': generator, 'form': form, 'generators': generators}
	return render(request, 'flashcard_generator/flashcard_generator.html', context)


@page.main('<int?:generator_id>')
def main_render(request, generator_id=None):
	generator = _generator_or_none(generator_id)
	return _render(request, generator, FlashcardGeneratorForm(instance=generator))


@page.action('<int?:generator_id>/save')
def save_generator(request, generator_id=None):
	generator = _generator_or_none(generator_id)
	form = FlashcardGeneratorForm(request.POST, instance=generator)
	if form.is_valid():
		generator = form.save()
		sync_generated_flashcards()
		return redirect('flashcard_generator_page.main_render', generator.id)
	else:
		return _render(request, generator, form)


@page.action('<int:generator_id>/delete')
def delete_generator(request, generator_id):
	get_object_or_404(FlashcardGenerator, pk=generator_id).delete()
	sync_generated_flashcards()
	return redirect('flashcard_generator_page.main_render')
