from itertools import starmap

from django.http import HttpResponseBadRequest
from django.shortcuts import render

from apps.website.components.knowledge_graph import GraphEdge, knowledge_graph
from apps.website.pages.page import Page
from core import hkm
from core.utils.fp import lmap

page = Page(name='knowledge_playground_page', base_route='knowledge/playground')


def graph_edges(facts):
	entities = set(hkm.get_all_entities())
	return list(
		starmap(
			lambda subject, predicate, object_: GraphEdge(subject, predicate, object_, object_ in entities, ''),
			facts,
		)
	)


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


@page.partial('row-graph')
def row_graph(request):
	query = request.GET.get('query', '')
	row = request.GET.get('row', '')
	try:
		results = hkm.run_query(query)
	except hkm.QueryError as error:
		return HttpResponseBadRequest(str(error))
	if not row.isdecimal() or int(row) >= len(results):
		return HttpResponseBadRequest('Invalid row')
	graph = knowledge_graph(graph_edges(hkm.matched_facts(query, [results[int(row)]])))
	return render(request, 'knowledge_playground/partial_row_graph.html', {'knowledge_graph': graph})
