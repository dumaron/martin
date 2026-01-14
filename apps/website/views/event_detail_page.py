from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.models import Event


@login_required
@require_GET
def main_render(request, event_id):
	event = get_object_or_404(Event, pk=event_id)
	documents = event.documents.all()
	return render(request, 'event_detail.html', {'event': event, 'documents': documents})
