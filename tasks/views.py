from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from datetime import datetime, timedelta
from .models import DailySuggestion, Project, Todo
from django.db.models import Q



@login_required
@require_GET
def root_page(request):
	return redirect('daily_suggestions_list')


@login_required
@require_GET
def daily_suggestion_detail(request, date=None):
	"""
	Gets the daily suggestion specified by the date in the request, or creates a new one if it doesn't exist and the
	date is not in the past.
	"""

	today_date = datetime.now().date().strftime('%Y-%m-%d')
	tomorrow_date = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')

	if date is None:
		return render(
			request, 'daily_suggestions/detail.html', {'today_date': today_date, 'tomorrow_date': tomorrow_date}
		)

	date = datetime.strptime(date, '%Y-%m-%d').date()
	daily_suggestion = DailySuggestion.objects.filter(date=date).first()

	if daily_suggestion is None:
		if date < datetime.now().date():
			return render(
				request,
				'daily_suggestions/detail.html',
				{
					'message': 'Cannot create a daily suggestion in the past',
					'today_date': today_date,
					'tomorrow_date': tomorrow_date,
				},
			)
		daily_suggestion = DailySuggestion(date=date)
		daily_suggestion.save()

	active_projects = Project.objects.filter(status=Project.Statuses.ACTIVE, todo__status=Todo.Statuses.TODO).distinct()

	return render(
		request,
		'daily_suggestions/detail.html',
		{
			'daily_suggestion': daily_suggestion,
			'today_date': today_date,
			'tomorrow_date': tomorrow_date,
			'projects': active_projects,
		},
	)


@login_required
@require_POST
def pick_todo(request, date):
	"""
	Handles the HTMX request for picking a Todo for the daily suggestion
	"""

	date = datetime.strptime(date, '%Y-%m-%d').date()
	daily_suggestion = get_object_or_404(DailySuggestion, pk=date)
	project_id = request.POST.get('project')
	criteria = request.POST.get('criteria')

	filters = [
		# The Todo should not have been completed or deleted
		Q(status=Todo.Statuses.TODO),
		# The Todo should not have been already picked for this daily suggestion
		~Q(pk__in=daily_suggestion.picked_todos.all()),
		# The Todo should be valid from now on, or have no validity period at all
		Q(valid_from__gte=datetime.now()) | Q(valid_from__isnull=True),
		# The Todo should not be part of the daily suggestion already
		~Q(pk__in=daily_suggestion.added_todos.all())
	]

	if criteria == 'deadline':
		filters.append(Q(deadline__isnull=False))

	if project_id != 'all':
		filters.append(Q(project_id=project_id))

	todo = Todo.objects.filter(*filters).order_by(criteria).first()

	if todo is None:
		# Returning an empty row is not the best feedback for hinting me that the search returned no Todo, I agree
		# It's good enough for now, while I'm still defining the basic interactions with Martin UI
		return render(request, 'daily_suggestions/pick_todo_empty.html')

	daily_suggestion.picked_todos.add(todo, through_defaults={})
	daily_suggestion.save()

	return render(request, 'daily_suggestions/pick_todo.html', {'todo': todo, 'date': date})


@login_required
@require_POST
def add_todo_to_daily_suggestion(request, date):
	"""
	Makes a Todo part of the daily suggestion (as "added" instead of "picked")
	"""

	date = datetime.strptime(date, '%Y-%m-%d').date()
	daily_suggestion = get_object_or_404(DailySuggestion, pk=date)
	todo = get_object_or_404(Todo, pk=request.POST.get('todo'))

	daily_suggestion.added_todos.add(todo, through_defaults={})
	daily_suggestion.picked_todos.remove(todo)
	daily_suggestion.save()

	return redirect('daily_suggestions_detail', date=date)
