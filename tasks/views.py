from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from datetime import datetime
from .models import DailySuggestion


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
	if date is None:
		return render(request, 'daily_suggestions/detail.html', {})

	date = datetime.strptime(date, '%Y-%m-%d').date()
	daily_suggestion = DailySuggestion.objects.filter(date=date).first()

	if daily_suggestion is None:
		if date < datetime.now().date():
			return render(
				request, 'daily_suggestions/detail.html', {'message': 'Cannot create a daily suggestion in the past'}
			)
		daily_suggestion = DailySuggestion(date=date)
		daily_suggestion.save()

	return render(request, 'daily_suggestions/detail.html', {'daily_suggestion': daily_suggestion})
