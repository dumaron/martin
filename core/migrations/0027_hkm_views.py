from django.db import migrations

# The HKM read layer queries two SQL views (hkm_current_facts, hkm_inferred_facts). Their DDL lives in
# core/hkm/views_sql.py (single source) and is also (re)created by a post_migrate signal — so the views
# exist even under settings.test, which disables migrations and builds the schema directly from the models.


def forwards(apps, schema_editor):
	from core.hkm.views_sql import create_views

	create_views(schema_editor.connection)


def backwards(apps, schema_editor):
	from core.hkm.views_sql import drop_views

	drop_views(schema_editor.connection)


class Migration(migrations.Migration):
	dependencies = [('core', '0026_predicaterule')]

	operations = [migrations.RunPython(forwards, backwards)]
