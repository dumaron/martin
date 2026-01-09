from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.models import Memory


@login_required
@require_GET
def main_render(request):
	"""
	TODO write a description
	"""

	try:
		selected_memory = Memory.select_memory_for_today()
	except (IndexError, Exception):
		selected_memory = None

	return render(request, 'home.html', {'memory': selected_memory})
