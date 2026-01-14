from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.website import views

"""
After some back and forth on what URLs should represent, I decided to go with an approach where they represent HTML
pages and actions (intended as form submit). So they are more representation-oriented than model-oriented. They take
inspiration more from the old PHP world than the REST approach which appeared a couple years after the first.

Everything is coupled in a reasonable way IMHO:
	>>> code is shaped after how the user (me) will use the application. <<<

Enjoy the benefit of not having to make everything generic: too much decoupling can be harmful in context where it's not
needed. If more "frontends" (intended as API, telegram bots, etc.) will be added, then we might have an actual reason to
rework coupling.

I know that the URLs nesting structure is somewhat incorrect. After all, why putting things under `/pages`
if no `/pages` page exists? But I think it helps me reason for now. If you notice, URls also don't match with the
breadcrumbs, which don't match with the navigation menu. Things are moving a lot, I'm learning and reasoning, keep peace
with things being messy and not perfect.

"""

urlpatterns = [
	path(route='admin/', view=admin.site.urls),
	path(route='accounts/', view=include('django.contrib.auth.urls')),
	#
	#
	# HOME PAGE ---------------------------------------------------------------------------------------------------------
	#
	path(route='', view=views.welcome_page.main_render, name='welcome_page.main_render'),
	#
	#
	# PAIR TRANSACTIONS PAGE --------------------------------------------------------------------------------------------
	#
	path(
		route='flows/pair-transactions/pair-transactions',
		view=views.pair_transactions_page.pair_transactions,
		name='pair_transactions_page.actions.pair_transactions',
	),
	path(
		route='flows/pair-transactions/snooze-bank-transaction',
		view=views.pair_transactions_page.snooze_bank_transaction,
		name='pair_transactions_page.actions.snooze_bank_transaction',
	),
	path(
		route='flows/pair-transactions/link-duplicate-bank-transactions',
		view=views.pair_transactions_page.link_duplicate_bank_transaction,
		name='pair_transactions_page.actions.link_duplicate_bank_transactions',
	),
	path(
		route='flows/pair-transactions/create-ynab-transaction',
		view=views.pair_transactions_page.create_ynab_transaction,
		name='pair_transactions_page.actions.create_ynab_transaction',
	),
	path(
		route='flows/pair-transactions/<str:kind>',
		view=views.pair_transactions_page.pair_transactions_page,
		name='pair_transactions_page.main_render',
	),
	#
	#
	# PROCESS INBOXES PAGE ----------------------------------------------------------------------------------------------
	#
	path(
		route='flows/process-inboxes',
		view=views.process_inboxes_page.process_inboxes_page,
		name='process_inboxes_page.main_render',
	),
	path(
		route='flows/process-inboxes/process-inbox',
		view=views.process_inboxes_page.process_inbox,
		name='process_inboxes_page.actions.process_inbox',
	),
	#
	#
	# SIMPLE TASKS PAGE -------------------------------------------------------------------------------------------------
	#
	path(
		route='pages/simple-tasks',
		view=views.simple_tasks_page.simple_tasks_page,
		name='simple_tasks_page.main_render',
	),
	path(
		route='pages/simple-tasks/create-task',
		view=views.simple_tasks_page.task_create,
		name='simple_tasks_page.actions.create_task',
	),
	path(
		route='pages/simple-tasks/mark-as-completed',
		view=views.simple_tasks_page.mark_task_as_completed,
		name='simple_tasks_page.actions.mark_task_as_completed',
	),
	path(
		route='pages/simple-tasks/abort-task',
		view=views.simple_tasks_page.abort_task,
		name='simple_tasks_page.actions.abort_task',
	),
	#
	#
	# CAPTURE INBOX PAGE ------------------------------------------------------------------------------------------------
	#
	path(
		route='pages/create-inbox-item',
		view=views.capture_inbox_page.main_render,
		name='capture_inbox_page.main_render',
	),
	path(
		route='pages/create-inbox-item/create',
		view=views.capture_inbox_page.capture_inbox_item,
		name='capture_inbox_page.actions.capture_inbox_item',
	),
	#
	#
	# DAILY SUGGESTIONS INTRO PAGE --------------------------------------------------------------------------------------
	#
	path(
		route='pages/daily-suggestions',
		view=views.daily_suggestions_intro_page.daily_suggestions_intro_page,
		name='daily_suggestions_intro_page.main_render',
	),
	#
	#
	# DAILY SUGGESTION DETAIL -------------------------------------------------------------------------------------------
	#
	path(
		route='pages/daily-suggestions/<str:date>',
		view=views.daily_suggestion_detail.main_render,
		name='daily_suggestions_editor_page.main_render',
	),
	path(
		route='pages/daily-suggestions/<str:date>/save',
		view=views.daily_suggestion_detail.save_daily_suggestion,
		name='daily_suggestions_editor_page.actions.save_daily_suggestion',
	),
	path(
		route='pages/daily-suggestions/<str:date>/pdf',
		view=views.daily_suggestion_detail.daily_suggestion_pdf,
		name='daily_suggestions_editor_page.actions.daily_suggestion_pdf',
	),
	#
	#
	# BANK EXPORT IMPORT PAGE -------------------------------------------------------------------------------------------
	#
	path(
		route='pages/import-bank-export',
		view=views.bank_export_import_page.main_render,
		name='import_bank_export_page.main_render',
	),
	path(
		route='pages/import-bank-export/import',
		view=views.bank_export_import_page.import_bank_export,
		name='import_bank_export_page.actions.import_bank_export',
	),
	#
	#
	# YNAB INTEGRATION PAGE ---------------------------------------------------------------------------------------------
	#
	path(
		route='integrations/ynab',
		view=views.ynab_integration_page.main_render,
		name='ynab_integration_page.main_render',
	),
	path(
		route='integrations/ynab/synchronize-categories',
		view=views.ynab_integration_page.synchronize_categories,
		name='ynab_integration_page.actions.synchronize_categories',
	),
	path(
		route='integrations/ynab/sync',
		view=views.ynab_integration_page.sync,
		name='ynab_integration_page.actions.sync',
	),
	#
	#
	# BANK FILE IMPORT LIST PAGE ----------------------------------------------------------------------------------------
	#
	path(
		route='models/bank-file-import',
		view=views.bank_file_import_list_page.main_render,
		name='bank_file_import_list_page.main_render',
	),
	#
	#
	# BANK FILE IMPORT DETAIL PAGE --------------------------------------------------------------------------------------
	#
	path(
		route='models/bank-file-import/<int:bank_file_import_id>',
		view=views.bank_file_import_detail_page.main_render,
		name='bank_file_import_detail_page.main_render',
	),
	#
	#
	# BANK TRANSACTION LIST PAGE ----------------------------------------------------------------------------------------
	#
	path(
		route='models/bank-transaction',
		view=views.bank_transaction_list_page.main_render,
		name='bank_transaction_list_page.main_render',
	),
	#
	#
	# BANK TRANSACTION DETAIL PAGE --------------------------------------------------------------------------------------
	#
	path(
		route='models/bank-transaction/<int:bank_transaction_id>',
		view=views.bank_transaction_detail_page.main_render,
		name='bank_transaction_detail_page.main_render',
	),
	#
	#
	# YNAB TRANSACTION DETAIL PAGE --------------------------------------------------------------------------------------
	#
	path(
		route='models/ynab-transaction/<str:ynab_transaction_id>',
		view=views.ynab_transaction_detail_page.main_render,
		name='ynab_transaction_detail_page.main_render',
	),
	#
	#
	# EVENT LIST PAGE ---------------------------------------------------------------------------------------------------
	#
	path(route='models/event', view=views.event_list_page.main_render, name='event_list_page.main_render'),
	#
	#
	# EVENT CREATE PAGE -------------------------------------------------------------------------------------------------
	#
	path(
		route='models/event/create', view=views.event_create_page.main_render, name='event_create_page.main_render'
	),
	path(
		route='models/event/create-action',
		view=views.event_create_page.create_event,
		name='event_create_page.actions.create_event',
	),
	#
	#
	# EVENT DETAIL PAGE -------------------------------------------------------------------------------------------------
	#
	path(
		route='models/event/<int:event_id>',
		view=views.event_detail_page.main_render,
		name='event_detail_page.main_render',
	),
	#
	#
	# DOCUMENT LIST PAGE ------------------------------------------------------------------------------------------------
	#
	path(
		route='models/document', view=views.document_list_page.main_render, name='document_list_page.main_render'
	),
	#
	#
	# DOCUMENT CREATE PAGE ----------------------------------------------------------------------------------------------
	#
	path(
		route='models/document/create',
		view=views.document_create_page.main_render,
		name='document_create_page.main_render',
	),
	path(
		route='models/document/create-action',
		view=views.document_create_page.create_document,
		name='document_create_page.actions.create_document',
	),
	#
	#
	# DOCUMENT DETAIL PAGE ----------------------------------------------------------------------------------------------
	#
	path(
		route='models/document/<int:document_id>',
		view=views.document_detail_page.main_render,
		name='document_detail_page.main_render',
	),
	#
	#
	# PROJECT LIST PAGE -------------------------------------------------------------------------------------------------
	#
	path(route='models/project', view=views.project_list_page.main_render, name='project_list_page.main_render'),
	#
	#
	# PROJECT CREATE PAGE -----------------------------------------------------------------------------------------------
	#
	path(
		route='models/project/create',
		view=views.project_create_page.main_render,
		name='project_create_page.main_render',
	),
	path(
		route='models/project/create-action',
		view=views.project_create_page.create_project,
		name='project_create_page.actions.create_project',
	),
	#
	#
	# PROJECT DETAIL PAGE -----------------------------------------------------------------------------------------------
	#
	path(
		route='models/project/<int:project_id>',
		view=views.project_detail_page.main_render,
		name='project_detail_page.main_render',
	),
	path(
		route='models/project/<int:project_id>/update-status',
		view=views.project_detail_page.update_status,
		name='project_detail_page.actions.update_status',
	),
	path(
		route='models/project/<int:project_id>/mark_task_complete',
		view=views.project_detail_page.mark_task_complete,
		name='project_detail_page.actions.mark_task_complete',
	),
	path(
		route='models/project/<int:project_id>/add-task-form',
		view=views.project_detail_page.add_task_form,
		name='project_detail_page.partials.add_task_form',
	),
	path(
		route='models/project/<int:project_id>/create-task',
		view=views.project_detail_page.create_task,
		name='project_detail_page.actions.create_task',
	),
	path(
		route='models/project/<int:project_id>/add-subproject-form',
		view=views.project_detail_page.add_subproject_form,
		name='project_detail_page.partials.add_subproject_form',
	),
	path(
		route='models/project/<int:project_id>/create-subproject',
		view=views.project_detail_page.create_subproject,
		name='project_detail_page.actions.create_subproject',
	),
	path(
		route='models/project/mark-tasks-complete',
		view=views.project_detail_page.mark_tasks_complete,
		name='project_detail_page.actions.mark_tasks_complete',
	),
	#
	#
	#
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
