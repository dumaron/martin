from django.test import TestCase

from core import hkm
from core.hkm.models import PredicateRule


def _apply_facts(triples):
	hkm.apply_transaction(hkm.create_draft_transaction(triples))


class RunQueryTest(TestCase):
	def test_required_rows_match_only_where_every_row_does(self):
		_apply_facts(
			[
				('lem', 'first_name', 'Stanisław'),
				('lem', 'last_name', 'Lem'),
				('calvino', 'first_name', 'Italo'),
			]
		)

		rows = hkm.run_query("""
			$p, first_name, $fn
			$p, last_name, $ln
		""")

		self.assertEqual(rows, [{'p': 'lem', 'fn': 'Stanisław', 'ln': 'Lem'}])

	def test_optional_row_keeps_the_result_when_the_graph_lacks_it(self):
		_apply_facts(
			[
				('lem', 'name', 'Stanisław Lem'),
				('lem', 'wrote', 'solaris'),
				('calvino', 'name', 'Italo Calvino'),
			]
		)

		rows = hkm.run_query("""
			$p, name, $name
			$p, ?wrote, $b
		""")

		self.assertEqual(
			rows,
			[
				{'p': 'calvino', 'name': 'Italo Calvino', 'b': None},
				{'p': 'lem', 'name': 'Stanisław Lem', 'b': 'solaris'},
			],
		)

	def test_rows_match_edges_implied_by_predicate_rules(self):
		PredicateRule.objects.create(source_predicate='father_of', implied_predicate='child_of', flip=True)
		_apply_facts(
			[
				('samuel', 'father_of', 'stanislaw'),
				('samuel', 'name', 'Samuel Lem'),
			]
		)

		rows = hkm.run_query("""
			$c, child_of, $f
			$f, name, $father
		""")

		self.assertEqual(rows, [{'c': 'stanislaw', 'f': 'samuel', 'father': 'Samuel Lem'}])

	def test_returns_one_row_per_match(self):
		_apply_facts(
			[
				('lem', 'wrote', 'solaris'),
				('lem', 'wrote', 'the_cyberiad'),
				('calvino', 'wrote', 'invisible_cities'),
				('solaris', 'name', 'Solaris'),
				('the_cyberiad', 'name', 'The Cyberiad'),
				('invisible_cities', 'name', 'Invisible Cities'),
			]
		)

		rows = hkm.run_query("""
			$p, wrote, $b
			$b, name, $title
		""")

		self.assertEqual(
			rows,
			[
				{'p': 'calvino', 'b': 'invisible_cities', 'title': 'Invisible Cities'},
				{'p': 'lem', 'b': 'solaris', 'title': 'Solaris'},
				{'p': 'lem', 'b': 'the_cyberiad', 'title': 'The Cyberiad'},
			],
		)

	def test_returns_nothing_when_no_entity_matches_every_row(self):
		_apply_facts(
			[
				('lem', 'first_name', 'Stanisław'),
				('calvino', 'last_name', 'Calvino'),
			]
		)

		rows = hkm.run_query("""
			$p, first_name, $fn
			$p, last_name, $ln
		""")

		self.assertEqual(rows, [])
