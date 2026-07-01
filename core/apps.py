from django.apps import AppConfig


class FinancesConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'core'

	def ready(self):
		from django.db.models.signals import post_migrate

		post_migrate.connect(create_hkm_views, sender=self)


def create_hkm_views(sender, using, **kwargs):
	# The HKM read layer queries SQL views (hkm_current_facts, hkm_inferred_facts). They are created by
	# migration 0027 during a normal `migrate`, but settings.test disables migrations and builds the schema
	# directly from the models, which would leave the views missing. Recreating them here — after the schema
	# is built, in any environment — guarantees the read layer works. Skipped if the tables they depend on
	# aren't present yet (e.g. a partial or backward migrate).
	from django.db import connections

	from core.hkm.views_sql import create_views

	connection = connections[using]
	required = {'hkm_facts', 'hkm_transactions', 'hkm_retractions', 'hkm_predicate_rules'}
	if required <= set(connection.introspection.table_names()):
		create_views(connection)
