# Single source of truth for the HKM SQL views (hkm_current_facts, hkm_inferred_facts).
#
# They are created by migration 0027 during a normal `migrate`. But settings.test disables migrations and
# builds the schema straight from the models — so the RunSQL/RunPython never runs and the views would be
# missing, breaking every read in queries.py. A post_migrate signal (see core/apps.py) therefore also calls
# create_views, so the views exist in every environment. Both paths delegate here, keeping the DDL in one
# place.

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


def create_views(connection):
	# Drop first so the views always match the definitions above (idempotent across repeated runs). Create
	# current before inferred, since inferred is built on top of it.
	with connection.cursor() as cursor:
		cursor.execute(DROP_INFERRED_FACTS)
		cursor.execute(DROP_CURRENT_FACTS)
		cursor.execute(CREATE_CURRENT_FACTS)
		cursor.execute(CREATE_INFERRED_FACTS)


def drop_views(connection):
	with connection.cursor() as cursor:
		cursor.execute(DROP_INFERRED_FACTS)
		cursor.execute(DROP_CURRENT_FACTS)
