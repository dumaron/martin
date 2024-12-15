from django.urls import path

from .views import daily_suggestion_detail, root_page

urlpatterns = [
	path('', root_page, name='tasks_root_page'),
	#
	# Daily suggestions
	path('daily-suggestions/', daily_suggestion_detail, name='daily_suggestions_list'),
	path('daily-suggestions/<str:date>/', daily_suggestion_detail, name='daily_suggestions_detail'),
]
