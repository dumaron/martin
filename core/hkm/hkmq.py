import re
from dataclasses import dataclass
from itertools import chain

from django.db import connection

from core.utils.fp import lfilter, lmap, separate

RELATIONS = ('hkm_current_facts', 'hkm_inferred_facts')
VARIABLE = re.compile(r'\$[A-Za-z_][A-Za-z0-9_]*')
ELEMENT = re.compile(r'\s*(?:"(?P<quoted>(?:[^"]|"")*)"|(?P<plain>[^,"]*))\s*(?P<end>,|$)')


class QueryError(ValueError):
	pass


@dataclass(frozen=True)
class Element:
	text: str
	quoted: bool
	column: int


@dataclass(frozen=True)
class Term:
	text: str
	is_variable: bool


@dataclass(frozen=True)
class Row:
	subject: Term
	predicate: str
	object: Term
	optional: bool
	line: int

	def terms(self):
		return self.subject, self.object

	def variables(self):
		return {term.text for term in self.terms() if term.is_variable}


def error(line, message, column=None):
	position = f'Line {line}, column {column}' if column else f'Line {line}'
	return QueryError(f'{position}: {message}')


def split_elements(text, line):
	elements = []
	position = 0
	while True:
		match = ELEMENT.match(text, position)
		if match is None:
			rest = text[position:]
			column = position + len(rest) - len(rest.lstrip()) + 1
			raise error(line, 'quotes must wrap a whole element, and a " inside one is written ""', column)
		if match['quoted'] is not None:
			elements.append(Element(match['quoted'].replace('""', '"'), True, match.start('quoted')))
		else:
			elements.append(Element(match['plain'].strip(), False, match.start('plain') + 1))
		if not match['end']:
			return elements
		position = match.end()


def term(element):
	if not element.quoted and VARIABLE.fullmatch(element.text):
		return Term(element.text[1:], True)
	return Term(element.text, False)


def parse_row(line, text):
	elements = split_elements(text, line)
	if len(elements) != 3:
		raise error(line, f'a row has 3 elements separated by commas, this one has {len(elements)}')
	empty = lfilter(lambda element: not element.quoted and not element.text, elements)
	if empty:
		raise error(line, 'empty element', empty[0].column)

	subject, predicate, object_ = elements
	optional = not predicate.quoted and predicate.text.startswith('?')
	name = predicate.text[1:].strip() if optional else predicate.text
	if optional and not name:
		raise error(line, 'a ? needs a predicate after it', predicate.column)
	if not predicate.quoted and VARIABLE.fullmatch(name):
		raise error(line, 'a predicate cannot be a variable', predicate.column)
	return Row(term(subject), name, term(object_), optional, line)


def parse(query):
	lines = enumerate(query.splitlines(), start=1)
	return lmap(lambda numbered: parse_row(*numbered), filter(lambda numbered: numbered[1].strip(), lines))


def attach(ordered, bound, pending):
	if not pending:
		return ordered
	row = next(filter(lambda candidate: candidate.variables() & bound, pending), None)
	if row is None and pending[0].optional:
		raise error(pending[0].line, "this optional row doesn't connect to the rest of the query")
	if row is None:
		raise error(pending[0].line, "this row doesn't share a variable with the other rows without ?")
	if row.optional and row.variables() <= bound:
		raise error(row.line, 'this optional row brings no new variable')
	return attach([*ordered, row], bound | row.variables(), lfilter(lambda other: other is not row, pending))


def order_rows(rows):
	constant = lfilter(lambda row: not row.variables(), rows)
	if constant:
		raise error(constant[0].line, 'a row needs at least one variable')
	required, optional = separate(lambda row: not row.optional, rows)
	if not required:
		raise QueryError('A query needs at least one row without ?')

	core = attach([required[0]], required[0].variables(), required[1:])
	return attach(core, set().union(*map(Row.variables, core)), optional)


def compile_query(rows, relation):
	if relation not in RELATIONS:
		raise ValueError(f'Unknown relation: {relation}')

	sites = {}
	joins, join_params = [], []
	where, where_params = [], []
	for index, row in enumerate(order_rows(rows)):
		alias = f't{index}'
		conditions, params = [f'{alias}.predicate = %s'], [row.predicate]
		for column, value in (('subject', row.subject), ('object', row.object)):
			reference = f'{alias}.{column}'
			if not value.is_variable:
				conditions.append(f'{reference} = %s')
				params.append(value.text)
			elif value.text in sites:
				conditions.append(f'{reference} = {sites[value.text]}')
			else:
				sites[value.text] = reference

		if index == 0:
			where, where_params = conditions, params
		else:
			join = 'LEFT JOIN' if row.optional else 'JOIN'
			joins.append(f'{join} {relation} {alias} ON {" AND ".join(conditions)}')
			join_params += params

	variables = filter(lambda value: value.is_variable, chain.from_iterable(map(Row.terms, rows)))
	columns = list(dict.fromkeys(map(lambda value: value.text, variables)))
	sql = ' '.join(
		[
			f'SELECT DISTINCT {", ".join(map(sites.get, columns))}',
			f'FROM {relation} t0',
			*joins,
			f'WHERE {" AND ".join(where)}',
			f'ORDER BY {", ".join(map(str, range(1, len(columns) + 1)))}',
		]
	)
	return sql, join_params + where_params, columns


def run_query(query, relation='hkm_inferred_facts'):
	sql, params, columns = compile_query(parse(query), relation)
	with connection.cursor() as cursor:
		cursor.execute(sql, params)
		return lmap(lambda values: dict(zip(columns, values)), cursor.fetchall())
