from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.models import Inbox


class InboxForm(forms.ModelForm):
	class Meta:
		model = Inbox
		fields = ['content']
		widgets = {'content': forms.Textarea(attrs={'rows': 4, 'placeholder': ''})}



@login_required
def capture_inbox(request):
	# TODO split this into GET and POST
	creation_success = False

	if request.method == 'POST':
		form = InboxForm(request.POST)
		if form.is_valid():
			form.save()
			creation_success = True

	new_creation_form = InboxForm()
	return render(
		request, 'inbox_create.html', {'form': new_creation_form, 'creation_success': creation_success}
	)
