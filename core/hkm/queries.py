from django.db.models import Count, F, Q

from core.hkm.models import CurrentFact, Fact, InferredFact, Retraction, Transaction

# HKM reads go through the two SQL views, hkm_current_facts and hkm_inferred_facts, which CurrentFact and
# InferredFact map onto as unmanaged models. The knowledge base is a small, fixed set of graph queries, and
# inference (the UNION today, recursive closure later) lives more naturally in SQL than in queryset chains —
# but the SQL belongs to the view definitions (core/hkm/views_sql.py), which leaves the reads below as plain
# querysets. Writes stay in the ORM as well, see mutations.py.
#
# Every function here returns lists of plain dicts (or of values), not model instances or lazy querysets: the
# callers are page views and templates walking rows, and nothing further down composes a query.

# The graph rows both inferred-fact queries return, in the order the columns mean something to a reader.
INFERRED_FIELDS = ('subject', 'predicate', 'object', 'origin', 'source_fact_id')


def get_all_entities():
	# Distinct subjects of the inferred graph. (With no rules defined this equals the subjects of current
	# facts; rules that flip an edge can surface an entity that was previously only an object.)
	return list(InferredFact.objects.order_by('subject').values_list('subject', flat=True).distinct())


def get_used_predicates():
	# Distinct predicates appearing in the inferred graph — feeds the predicate picker on the create page.
	return list(InferredFact.objects.order_by('predicate').values_list('predicate', flat=True).distinct())


def get_facts(subject):
	# Outgoing edges: rows of the inferred graph where `subject` is the subject. Each row carries `origin`
	# ('asserted' | 'implied') and `source_fact_id` so a derived edge can be marked and traced.
	return list(
		InferredFact.objects.filter(subject=subject).order_by('predicate', 'object').values(*INFERRED_FIELDS)
	)


def get_incoming_facts(entity):
	# Incoming edges: rows of the inferred graph where `entity` is the object (the backlinks that make the
	# knowledge base navigable as a graph).
	return list(
		InferredFact.objects.filter(object=entity).order_by('subject', 'predicate').values(*INFERRED_FIELDS)
	)


def get_retractable_facts():
	# The facts a new retraction may point at: exactly the current ones. Only applied transactions count here,
	# which is the whole of what `hkm_current_facts` means — a fact asserted by a draft is not real yet, and a
	# retraction staged by a draft has not removed anything yet. Returned as dicts with the fact id, which a
	# new retraction references.
	#
	# So a fact stays on offer while some draft holds a pending retraction of it, including the draft being
	# edited (which is what lets that draft show its own selection back). Two drafts can therefore both stage
	# the retraction of one fact, and the second one saved raises: `Retraction.fact` is a primary key, so the
	# intent to retract a fact can only be stored once. Accepted — offering the truth about what is current
	# beats hiding facts to dodge a clash between drafts.
	return list(
		CurrentFact.objects.order_by('subject', 'predicate', 'object').values(
			'id', 'subject', 'predicate', 'object'
		)
	)


def search_retractable_facts(query):
	# The retractable facts (see above) whose subject, predicate or object contains `query`, case-insensitively:
	# the same rows `get_retractable_facts` offers, narrowed to what someone is typing. Asserted and current, so
	# neither the inferred graph (an implied edge has no fact of its own for a retraction to point at) nor
	# anything a draft has asserted or an applied retraction has removed.
	#
	# `icontains` rather than a literal ILIKE: it is the portable spelling (this project runs on SQLite, which
	# has no ILIKE operator and whose LIKE is already case-insensitive for ASCII), and Django escapes the
	# wildcards inside the query itself, so typing '%' searches for a percent sign instead of matching all.
	#
	# A blank query matches nothing rather than everything — an emptied search box means no suggestions, where
	# `icontains=''` would answer with the whole of current knowledge.
	search = (query or '').strip()
	if not search:
		return []
	return list(
		CurrentFact.objects.filter(
			Q(subject__icontains=search) | Q(predicate__icontains=search) | Q(object__icontains=search)
		)
		.order_by('subject', 'predicate', 'object')
		.values('id', 'subject', 'predicate', 'object')
	)


def get_draft_transactions():
	# Unapplied drafts, oldest first — batches parked between "save" and "apply/discard", so they stay
	# reachable from the create page. Bookkeeping on a plain table rather than a graph query, so this one reads
	# Transaction directly instead of going through a view — and hands back model instances, the template
	# wanting real datetimes and the annotated counts.
	return (
		Transaction.objects.filter(applied_at=None)
		.annotate(fact_count=Count('facts', distinct=True), retraction_count=Count('retractions', distinct=True))
		.order_by('created_at')
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
	staged = list(
		Fact.objects.filter(transaction_id=transaction_id).order_by('id').values('subject', 'predicate', 'object')
	)
	additions = []
	for fact in staged:
		existing = list(
			CurrentFact.objects.filter(subject=fact['subject'], predicate=fact['predicate'])
			.values_list('object', flat=True)
			.distinct()
		)
		if fact['object'] in existing:
			additions.append({'fact': fact, 'status': 'duplicate', 'existing': []})
		elif existing:
			additions.append({'fact': fact, 'status': 'conflict', 'existing': existing})
		else:
			additions.append({'fact': fact, 'status': 'new', 'existing': []})

	# Facts this draft would retract, resolved back to their (subject, predicate, object) for display. Read from
	# Retraction and aliased across the relation, so a row reads like every other triple in here.
	retractions = list(
		Retraction.objects.filter(transaction_id=transaction_id)
		.order_by('fact__subject', 'fact__predicate', 'fact__object')
		.values(subject=F('fact__subject'), predicate=F('fact__predicate'), object=F('fact__object'))
	)
	return {'additions': additions, 'retractions': retractions}
