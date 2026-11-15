import subprocess
from dataclasses import dataclass

from django.urls import reverse
from django.utils.safestring import SafeString, mark_safe
from django.utils.text import Truncator

from core import hkm
from core.utils.fp import separate, unique

LITERAL_LABEL_LENGTH = 40

GRAPH_ATTRIBUTES = (
	'rankdir=LR',
	'bgcolor=transparent',
	'node [fontname=Helvetica fontsize=11]',
	'edge [fontname=Helvetica fontsize=10]',
)


@dataclass(frozen=True)
class GraphEdge:
	subject: str
	predicate: str
	object: str
	object_is_entity: bool
	kind: str


def quoted(text: str) -> str:
	return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


def object_node(edge: GraphEdge) -> str:
	if edge.object_is_entity:
		return edge.object
	return f'({edge.subject}, {edge.predicate}, {edge.object})'


def entity_statement(entity: str, focus: str | None) -> str:
	url = reverse('entity_detail_page.main_render', kwargs={'entity': entity})
	classes = 'entity focus' if entity == focus else 'entity'
	return f'{quoted(entity)} [href={quoted(url)} class={quoted(classes)}]'


def literal_statement(edge: GraphEdge) -> str:
	label = Truncator(edge.object).chars(LITERAL_LABEL_LENGTH)
	return (
		f'{quoted(object_node(edge))} [label={quoted(label)} shape=box class={quoted(f"literal {edge.kind}")}]'
	)


def edge_statement(edge: GraphEdge) -> str:
	return (
		f'{quoted(edge.subject)} -> {quoted(object_node(edge))} '
		f'[label={quoted(edge.predicate)} class={quoted(edge.kind)}]'
	)


def render_svg(dot: str) -> str:
	svg = subprocess.run(['dot', '-Tsvg'], input=dot, capture_output=True, encoding='utf-8', check=True).stdout
	return svg[svg.index('<svg') :]


def knowledge_graph(edges: list[GraphEdge], focus: str | None = None) -> SafeString | str:
	edges = list(unique(edges))
	if not edges:
		return ''

	entity_edges, literal_edges = separate(lambda edge: edge.object_is_entity, edges)
	entities = unique([*map(lambda edge: edge.subject, edges), *map(lambda edge: edge.object, entity_edges)])
	dot = '\n'.join(
		[
			'digraph {',
			*GRAPH_ATTRIBUTES,
			*map(lambda entity: entity_statement(entity, focus), entities),
			*map(literal_statement, literal_edges),
			*map(edge_statement, edges),
			'}',
		]
	)
	return mark_safe(render_svg(dot))


def review_edge(fact: dict, entities: set[str], kind: str) -> GraphEdge:
	return GraphEdge(fact['subject'], fact['predicate'], fact['object'], fact['object'] in entities, kind)


def review_graph(review: dict) -> SafeString | str:
	entities = set(hkm.get_all_entities()) | {addition['fact']['subject'] for addition in review['additions']}
	return knowledge_graph(
		[
			*map(
				lambda addition: review_edge(addition['fact'], entities, f'status-{addition["status"]}'),
				review['additions'],
			),
			*map(lambda fact: review_edge(fact, entities, 'status-retract'), review['retractions']),
		]
	)
