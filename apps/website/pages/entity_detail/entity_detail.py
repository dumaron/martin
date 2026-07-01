from django.shortcuts import render

from apps.website.pages.page import Page
from core import hkm
from core.utils.fp import lmap

page = Page(name='entity_detail_page', base_route='knowledge/entities/<path:entity>')


@page.main
def main_render(request, entity):
	# An entity has no row of its own — it exists only by being mentioned. So a detail view is just the two
	# directions of the facts that mention it: outgoing (entity as subject) and incoming (entity as object).
	known_entities = set(hkm.get_all_entities())

	# get_facts / get_incoming_facts return rows of the inferred graph as dicts, already ordered in SQL.
	outgoing = lmap(
		lambda fact: {
			'predicate': fact['predicate'],
			'object': fact['object'],
			'object_is_entity': fact['object'] in known_entities,
			'origin': fact['origin'],
		},
		hkm.get_facts(entity),
	)
	# Subjects of incoming facts are entities by definition (they are subjects somewhere), so always linkable.
	incoming = lmap(
		lambda fact: {'subject': fact['subject'], 'predicate': fact['predicate'], 'origin': fact['origin']},
		hkm.get_incoming_facts(entity),
	)

	context = {
		'entity': entity,
		'outgoing': outgoing,
		'incoming': incoming,
		'has_facts': bool(outgoing or incoming),
	}
	return render(request, 'entity_detail/entity_detail.html', context)
