from django.urls import path

from .views import daily_suggestion_detail, root_page, pick_todo, add_todo_to_daily_suggestion

urlpatterns = [
	path('', root_page, name='tasks_root_page'),
	#
	# Daily suggestions
	path('daily-suggestions/', daily_suggestion_detail, name='daily_suggestions_list'),
	path('daily-suggestions/<str:date>/', daily_suggestion_detail, name='daily_suggestions_detail'),
	path('daily-suggestions/<str:date>/pick-todo', pick_todo, name='pick_todo'),
	path('daily-suggestions/<str:date>/add-todo', add_todo_to_daily_suggestion, name='add_todo_to_daily_suggestion'),
]
