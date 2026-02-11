from django.shortcuts import render

from apps.website.pages.page import Page
from core.models import Memory

page = Page(name='welcome_page', base_route='')


@page.main
def main_render(request):
	"""
	TODO write a description
	"""

	try:
		selected_memory = Memory.select_memory_for_today()
	except (IndexError, Exception):
		selected_memory = None

	return render(request, 'welcome/welcome.html', {'memory': selected_memory})
