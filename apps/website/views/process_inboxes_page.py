from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from core.models import Inbox, Project


@login_required
@require_GET
def process_inboxes_page(request):
	# TODO add description
	# Get the oldest unprocessed inbox item
	oldest_inbox = Inbox.objects.filter(processed_at__isnull=True).order_by('created_at').first()
	projects = Project.objects.filter(status='active')

	return render(request, 'process_inboxes_page.html', {'inbox': oldest_inbox, 'projects': projects})


@login_required
@require_POST
def process_inbox(request, inbox_id):
	# TODO write description for process_inbox_item action
	inbox = get_object_or_404(Inbox, pk=inbox_id)
	inbox.processed_at = timezone.now()
	inbox.save()

	return redirect('process_inboxes_page')
