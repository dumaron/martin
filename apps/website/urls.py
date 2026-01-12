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
	path('admin/', admin.site.urls),
	path('accounts/', include('django.contrib.auth.urls')),
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
	path(route='pages/simple-tasks/abort-task', view=views.simple_tasks_page.abort_task, name='simple_tasks_page.actions.abort_task'),
	#
	#
	# ADD INBOX PAGE ----------------------------------------------------------------------------------------------------
	#
	path(route='pages/create-inbox-item', view=views.capture_inbox_item_page.capture_inbox, name='capture_inbox_page.main_render'),
	path(
		route='pages/create-inbox-item/create', view=views.capture_inbox_item_page.capture_inbox, name='capture_inbox_page.actions.capture_inbox_item'
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
	# -- CONTINUE FROM HERE --
	# This porting is takin too much time, I need to move forward with more important features
	# --
	#
	# IMPORT FILE PAGE --------------------------------------------------------------------------------------------------
	#
	path(
		'pages/import-bank-export',
		views.bank_export_import_page.import_bank_export_page,
		name='import_bank_export_page',
	),
	path(
		'pages/import-bank-export/import',
		views.bank_export_import_page.import_bank_export_page,
		name='import_bank_export',
	),
	#
	#
	# YNAB INTEGRATION PAGE ---------------------------------------------------------------------------------------------
	#
	path(
		route='integrations/ynab',
		view=views.ynab_integration_page.ynab_integration_page,
		name='ynab_integration_page',
	),
	path(
		route='integrations/ynab/synchronize-categories',
		view=views.ynab_integration_page.synchronize_ynab_categories,
		name='synchronize_ynab_categories',
	),
	path('integrations/ynab/sync', views.ynab_integration_page.ynab_sync, name='ynab_sync'),
	#
	#
	# BANK FILE IMPORT MODEL --------------------------------------------------------------------------------------------
	# I need to find a good way to centralize some of this view logic. Maybe with class-based views? Mah.
	#
	path(
		route='models/bank-file-import',
		view=views.bank_file_import_model.bank_file_import_list,
		name='bank_file_import_list',
	),
	path(
		route='models/bank-file-import/<int:bank_file_import_id>',
		view=views.bank_file_import_model.bank_file_import_detail,
		name='bank_file_import_detail',
	),
	#
	#
	# BANK TRANSACTION MODEL --------------------------------------------------------------------------------------------
	#
	path(
		'models/bank-transaction', views.bank_transaction_model.bank_transaction_list, name='bank_transaction_list'
	),
	path(
		'models/bank-transaction/<int:bank_transaction_id>',
		views.bank_transaction_model.bank_transaction_detail,
		name='bank_transaction_detail',
	),
	#
	#
	# YNAB TRANSACTION MODEL --------------------------------------------------------------------------------------------
	#
	path(
		'models/ynab-transaction/<str:ynab_transaction_id>',
		views.ynab_transaction_model.ynab_transaction_detail,
		name='ynab_transaction_detail',
	),
	#
	#
	# DOCUMENT MODEL ----------------------------------------------------------------------------------------------------
	#
	path(route='models/document', view=views.document_model.document_list, name='document_list'),
	path(
		route='models/document/create', view=views.document_model.document_create_page, name='document_create_page'
	),
	path(
		route='models/document/create-action', view=views.document_model.document_create, name='document_create'
	),
	path(
		route='models/document/<int:document_id>', view=views.document_model.document_detail, name='document_detail'
	),
	#
	#
	# PROJECT MODEL -----------------------------------------------------------------------------------------------------
	#
	path('models/project', views.project_model.project_list, name='project_list'),
	path('models/project/create', views.project_model.project_create, name='project_create'),
	path('models/project/<int:project_id>', views.project_model.project_detail, name='project_detail'),
	path(
		'models/project/<int:project_id>/update-status',
		views.project_model.project_update_status,
		name='update_project_status',
	),
	path(
		route='models/project/<int:project_id>/mark_task_complete',
		view=views.project_model.mark_task_as_completed,
		name='project_mark_task_complete_action',
	),
	path(
		route='models/project/<int:project_id>/add-task-form',
		view=views.project_model.get_add_task_form,
		name='get_add_task_form',
	),
	path(
		route='models/project/<int:project_id>/create-task',
		view=views.project_model.create_task,
		name='create_task_htmx',
	),
	path(
		route='models/project/<int:project_id>/add-subproject-form',
		view=views.project_model.get_add_subproject_form,
		name='get_add_subproject_form',
	),
	path(
		route='models/project/<int:project_id>/create-subproject',
		view=views.project_model.create_subproject,
		name='create_subproject_htmx',
	),
	path(
		route='models/project/mark-tasks-complete',
		view=views.project_model.mark_tasks_complete,
		name='mark_tasks_complete',
	),
	#
	#
	#
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
