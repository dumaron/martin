from django.urls import path
from .views import first_page, project_detail


urlpatterns = [
    path('projects/', first_page, name='tasks_first_page'),
    path('projects/<int:project_id>/', project_detail, name='project_detail'),
]
