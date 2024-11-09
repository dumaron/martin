from django.urls import path
from .views import *


urlpatterns = [
    # Project-based views
    path('projects/', first_page, name='tasks_first_page'),
    path('projects/<int:project_id>/', project_detail, name='project_detail'),

    # Flows
    path('flows/', flows_list, name='flows_list'),
    path('flows/max-priority', process_tasks_by_priority_flow, name='process_tasks_by_priority_flow'),
]
