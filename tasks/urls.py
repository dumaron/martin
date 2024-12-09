from django.urls import path

from .views import (
	first_page,
	flows_list,
	process_inbox,
	process_inboxes_flow,
	process_tasks_by_priority_flow,
	project_detail,
)

urlpatterns = [
	# Project-based views
	path('projects/', first_page, name='tasks_first_page'),
	path('projects/<int:project_id>/', project_detail, name='project_detail'),
	#
	# Inboxes
	path('inboxes/<int:inbox_id>/', process_inbox, name='process_inbox'),
	#
	# Flows
	path('flows/', flows_list, name='flows_list'),
	path('flows/max-priority', process_tasks_by_priority_flow, name='process_tasks_by_priority_flow'),
	path('flows/process-inboxes', process_inboxes_flow, name='process_inboxes_flow'),
]
