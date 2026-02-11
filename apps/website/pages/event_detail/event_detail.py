from django.shortcuts import get_object_or_404, render

from apps.website.pages.page import Page
from core.models import Event

page = Page(name='event_detail_page', base_route='models/event/<int:event_id>')


@page.main
def main_render(request, event_id):
	event = get_object_or_404(Event, pk=event_id)
	documents = event.documents.all()
	return render(request, 'event_detail/event_detail.html', {'event': event, 'documents': documents})
