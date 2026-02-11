from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.website.pages.page import Page
from core.models import Inbox, Project

page = Page(name='process_inboxes_page', base_route='flows/process-inboxes')


@page.main
def process_inboxes_page(request):
	# TODO add description
	# Get the oldest unprocessed inbox item
	oldest_inbox = Inbox.objects.filter(processed_at__isnull=True).order_by('created_at').first()
	projects = Project.objects.filter(status='active')

	return render(request, 'process_inboxes/process_inboxes.html', {'inbox': oldest_inbox, 'projects': projects})


@page.action('process-inbox')
def process_inbox(request):
	# TODO write description for process_inbox_item action

	inbox_id = int(request.POST.get('inbox_id'))
	inbox = get_object_or_404(Inbox, pk=inbox_id)
	inbox.processed_at = timezone.now()
	inbox.save()

	return redirect('process_inboxes_page.main_render')
