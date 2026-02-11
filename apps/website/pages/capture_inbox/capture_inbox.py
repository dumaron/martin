from django import forms
from django.shortcuts import render

from apps.website.pages.page import Page
from core.models import Inbox


class InboxForm(forms.ModelForm):
	class Meta:
		model = Inbox
		fields = ['content']
		widgets = {'content': forms.Textarea(attrs={'rows': 4, 'placeholder': ''})}


page = Page(name='capture_inbox_page', base_route='pages/create-inbox-item')


@page.main
def main_render(request):
	form = InboxForm()
	return render(request, 'capture_inbox/inbox_create.html', {'form': form, 'creation_success': False})


@page.action('create')
def capture_inbox_item(request):
	form = InboxForm(request.POST)
	if form.is_valid():
		form.save()
		# Redirect to the main render to show the success state
		return render(request, 'capture_inbox/inbox_create.html', {'form': InboxForm(), 'creation_success': True})
	return render(request, 'capture_inbox/inbox_create.html', {'form': form, 'creation_success': False})
