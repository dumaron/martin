from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.models import Inbox


class InboxForm(forms.ModelForm):
	class Meta:
		model = Inbox
		fields = ['content']
		widgets = {'content': forms.Textarea(attrs={'rows': 4, 'placeholder': ''})}


@login_required
@require_GET
def main_render(request):
	form = InboxForm()
	return render(request, 'inbox_create.html', {'form': form, 'creation_success': False})


@login_required
@require_POST
def capture_inbox_item(request):
	form = InboxForm(request.POST)
	if form.is_valid():
		form.save()
		# Redirect to the main render to show the success state
		return render(request, 'inbox_create.html', {'form': InboxForm(), 'creation_success': True})
	return render(request, 'inbox_create.html', {'form': form, 'creation_success': False})
