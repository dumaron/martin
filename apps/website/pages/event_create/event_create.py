from django import forms
from django.shortcuts import redirect, render

from apps.website.pages.page import Page
from core.models import Event


class EventForm(forms.ModelForm):
	class Meta:
		model = Event
		fields = ['description', 'date', 'time', 'documents']
		widgets = {
			'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Event description'}),
			'date': forms.DateInput(attrs={'type': 'date'}),
			'time': forms.TimeInput(attrs={'type': 'time'}),
			'documents': forms.SelectMultiple(attrs={'class': 'tom-select'}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['time'].required = False
		self.fields['time'].widget.attrs['required'] = False
		self.fields['documents'].required = False


page = Page(name='event_create_page', base_route='models/event')


@page.main('create')
def main_render(request):
	form = EventForm()
	return render(request, 'event_create/event_create.html', {'form': form})


@page.action('create-action')
def create_event(request):
	form = EventForm(request.POST)
	if form.is_valid():
		event = form.save()
		return redirect('event_detail_page.main_render', event_id=event.id)
	else:
		return render(request, 'event_create/event_create.html', {'form': form})
