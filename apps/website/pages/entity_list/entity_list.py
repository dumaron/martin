from django.shortcuts import render

from apps.website.pages.page import Page
from core.hkm import queries

page = Page(name='entity_list_page', base_route='knowledge/entities')


@page.main
def main_render(request):
	return render(request, 'entity_list/entity_list.html', {'entities': queries.entities()})
