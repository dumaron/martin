from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.models import Memory


@login_required
@require_GET
def martin_home_page(request):
	"""
	The Martin initial page. Tomorrow it'll contain pictures of the people I love, or inspiring quotes/images.
	Right now, I need to adapt.
	"""

	# Select a memory for today
	try:
		selected_memory = Memory.select_memory_for_today()
	except (IndexError, Exception):
		selected_memory = None

	return render(request, 'home.html', {'memory': selected_memory})
