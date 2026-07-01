from django.db import connection

# HKM reads go through raw SQL over the hkm_current_facts / hkm_inferred_facts views rather than the ORM.
# The knowledge base is a small, fixed set of graph queries, and inference (the UNION today, recursive
# closure later) lives more naturally in SQL than in queryset chains. Writes stay in the ORM (see
# mutations.py). All user-supplied values are passed as bound parameters (%s) — never interpolated.


def _rows(sql, params=()):
	# Run a read query and return each row as a dict keyed by column name.
	with connection.cursor() as cursor:
		cursor.execute(sql, params)
		columns = [column[0] for column in cursor.description]
		return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _column(sql, params=()):
	# Run a read query that selects a single column and return its values as a flat list.
	with connection.cursor() as cursor:
		cursor.execute(sql, params)
		return [row[0] for row in cursor.fetchall()]


def get_all_entities():
	# Distinct subjects of the inferred graph. (With no rules defined this equals the subjects of current
	# facts; rules that flip an edge can surface an entity that was previously only an object.)
	return _column('SELECT DISTINCT subject FROM hkm_inferred_facts ORDER BY subject')


def get_used_predicates():
	# Distinct predicates appearing in the inferred graph — feeds the predicate picker on the create page.
	return _column('SELECT DISTINCT predicate FROM hkm_inferred_facts ORDER BY predicate')


def get_facts(subject):
	# Outgoing edges: rows of the inferred graph where `subject` is the subject. Each row carries `origin`
	# ('asserted' | 'implied') and `source_fact_id` so a derived edge can be marked and traced.
	return _rows(
		'SELECT subject, predicate, object, origin, source_fact_id '
		'FROM hkm_inferred_facts WHERE subject = %s '
		'ORDER BY predicate, object',
		[subject],
	)


def get_incoming_facts(entity):
	# Incoming edges: rows of the inferred graph where `entity` is the object (the backlinks that make the
	# knowledge base navigable as a graph).
	return _rows(
		'SELECT subject, predicate, object, origin, source_fact_id '
		'FROM hkm_inferred_facts WHERE object = %s '
		'ORDER BY subject, predicate',
		[entity],
	)


def get_retractable_facts():
	# Current facts that can be cleanly retracted: applied, not already removed, and with no retraction at all
	# (not even a draft one — a fact's OneToOne retraction PK means it can be retracted at most once, so we
	# must not offer a fact that already has a retraction staged). Returned as dicts with the fact id, which a
	# new retraction references.
	return _rows(
		'SELECT id, subject, predicate, object '
		'FROM hkm_current_facts cf '
		'WHERE NOT EXISTS (SELECT 1 FROM hkm_retractions r WHERE r.fact_id = cf.id) '
		'ORDER BY subject, predicate, object'
	)


def review_transaction(transaction_id):
	# Preview the effect a still-draft transaction would have on current knowledge: what it would add and what
	# it would retract. The draft's own facts/retractions are unapplied, so they are absent from
	# hkm_current_facts; we read them straight from the base tables and compare against the asserted current
	# view (deliberately not the inferred graph — a review is judged against what you have asserted).
	#
	# Each addition is tagged:
	#   'duplicate' - the exact triple is already current
	#   'conflict'  - the same (subject, predicate) is current with a different object (see `existing`)
	#   'new'       - that (subject, predicate) is absent from current knowledge
	staged = _rows(
		'SELECT subject, predicate, object FROM hkm_facts WHERE transaction_id = %s ORDER BY id', [transaction_id]
	)
	additions = []
	for fact in staged:
		existing = _column(
			'SELECT DISTINCT object FROM hkm_current_facts WHERE subject = %s AND predicate = %s',
			[fact['subject'], fact['predicate']],
		)
		if fact['object'] in existing:
			additions.append({'fact': fact, 'status': 'duplicate', 'existing': []})
		elif existing:
			additions.append({'fact': fact, 'status': 'conflict', 'existing': existing})
		else:
			additions.append({'fact': fact, 'status': 'new', 'existing': []})

	# Facts this draft would retract, resolved back to their (subject, predicate, object) for display.
	retractions = _rows(
		'SELECT f.subject, f.predicate, f.object '
		'FROM hkm_retractions r JOIN hkm_facts f ON f.id = r.fact_id '
		'WHERE r.transaction_id = %s ORDER BY f.subject, f.predicate, f.object',
		[transaction_id],
	)
	return {'additions': additions, 'retractions': retractions}
