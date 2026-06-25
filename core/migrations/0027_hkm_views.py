from django.db import migrations

# Two layered, read-only SQL views that form the HKM read surface. They are created with raw SQL (not
# managed models): HKM reads go through hand-written SQL over these views rather than the ORM, because the
# knowledge base is a small fixed set of graph queries and inference reads more naturally as SQL.
#
# `hkm_current_facts` is the canonical "current knowledge": a fact counts only once its own transaction is
# applied, and it stops counting only once a retraction whose transaction is *also* applied removes it. A
# retraction staged inside an unapplied draft does not hide the fact yet (the draft lifecycle applies to
# both sides). This mirrors FactQuerySet.current().
CREATE_CURRENT_FACTS = """
CREATE VIEW hkm_current_facts AS
SELECT f.id, f.subject, f.predicate, f.object, f.transaction_id
FROM hkm_facts f
JOIN hkm_transactions t ON t.id = f.transaction_id
WHERE t.applied_at IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM hkm_retractions r
    JOIN hkm_transactions rt ON rt.id = r.transaction_id
    WHERE r.fact_id = f.id AND rt.applied_at IS NOT NULL
  )
"""

# `hkm_inferred_facts` is the navigable graph: every current fact (origin='asserted') together with the
# single-step implications produced by joining current facts to the rule table (origin='implied'). `flip`
# swaps subject and object for inverse/symmetric rules. With no rules defined the second branch is empty, so
# the view is exactly the current facts.
#
# The inner UNION ALL gathers both branches; the outer GROUP BY then collapses to exactly one row per
# (subject, predicate, object) triple — so a triple that is both asserted and implied (an inverse edge you
# also asserted by hand, or an identity-ish `p -> p` rule) appears once, not twice. `origin` resolves to
# 'asserted' whenever any source of the triple is asserted (asserted wins), else 'implied'; `source_fact_id`
# keeps one representative source fact for provenance. Termination is guaranteed by inference being
# single-step (one pass off asserted facts, no recursion) — not by any dedup.
CREATE_INFERRED_FACTS = """
CREATE VIEW hkm_inferred_facts AS
SELECT
  subject,
  predicate,
  object,
  CASE WHEN MAX(origin = 'asserted') = 1 THEN 'asserted' ELSE 'implied' END AS origin,
  MIN(source_fact_id) AS source_fact_id
FROM (
  SELECT
    cf.subject AS subject,
    cf.predicate AS predicate,
    cf.object AS object,
    'asserted' AS origin,
    cf.id AS source_fact_id
  FROM hkm_current_facts cf
  UNION ALL
  SELECT
    CASE WHEN pr.flip THEN cf.object ELSE cf.subject END AS subject,
    pr.implied_predicate AS predicate,
    CASE WHEN pr.flip THEN cf.subject ELSE cf.object END AS object,
    'implied' AS origin,
    cf.id AS source_fact_id
  FROM hkm_current_facts cf
  JOIN hkm_predicate_rules pr ON pr.source_predicate = cf.predicate
) edges
GROUP BY subject, predicate, object
"""

DROP_CURRENT_FACTS = 'DROP VIEW IF EXISTS hkm_current_facts'
DROP_INFERRED_FACTS = 'DROP VIEW IF EXISTS hkm_inferred_facts'


class Migration(migrations.Migration):
	dependencies = [('core', '0026_predicaterule')]

	operations = [
		# Create current first; inferred is built on top of it. Drop in reverse order.
		migrations.RunSQL(
			sql=[CREATE_CURRENT_FACTS, CREATE_INFERRED_FACTS], reverse_sql=[DROP_INFERRED_FACTS, DROP_CURRENT_FACTS]
		)
	]
