from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.website.forms import InboxForm
from core.models import Inbox, Project, Task


@login_required
def inbox_create(request):
	creation_success = False

	if request.method == 'POST':
		form = InboxForm(request.POST)
		if form.is_valid():
			form.save()
			creation_success = True

	new_creation_form = InboxForm()
	return render(request, 'inbox_create.html', {'form': new_creation_form, 'creation_success': creation_success})


@login_required
@require_GET
def flow_page(request):
	# Get the oldest unprocessed inbox item
	oldest_inbox = Inbox.objects.filter(processed_at__isnull=True).order_by('created_at').first()
	
	if not oldest_inbox:
		# TODO no, let's redirect to the flow page but with an empty message
		return redirect('inbox_list')
	
	projects = Project.objects.filter(status='active')
	return render(request, 'process_inboxes_page.html', {'inbox': oldest_inbox, 'projects': projects})


@login_required
@require_POST
def process_inbox_item(request, inbox_id):
	inbox = get_object_or_404(Inbox, pk=inbox_id)
	inbox.processed_at = timezone.now()
	inbox.save()

	return redirect('flow_page')