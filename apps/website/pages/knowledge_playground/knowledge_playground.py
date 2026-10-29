from django.shortcuts import render

from apps.website.pages.page import Page
from core import hkm
from core.utils.fp import lmap

page = Page(name='knowledge_playground_page', base_route='knowledge/playground')


@page.main
def main_render(request):
	query = request.GET.get('query', '')
	context = {'query': query, 'has_run': bool(query.strip())}
	if context['has_run']:
		try:
			rows = hkm.run_query(query)
			context['columns'] = list(rows[0]) if rows else []
			context['rows'] = lmap(lambda row: list(row.values()), rows)
		except hkm.QueryError as error:
			context['error'] = str(error)
	return render(request, 'knowledge_playground/knowledge_playground.html', context)
