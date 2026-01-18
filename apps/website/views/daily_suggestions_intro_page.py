import datetime

from django.contrib.auth.decorators import login_required
from itertools import groupby
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.models import DailySuggestion


@login_required
@require_GET
def daily_suggestions_intro_page(request):
	today = datetime.date.today().strftime('%Y-%m-%d')
	tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
	previous_entries = DailySuggestion.objects.filter(date__lte=today).order_by('-date').all()
	days_in_month = list(range(1, 32))
	grouped_by_month = {}
	for month, suggestions in groupby(previous_entries, key=lambda ds: ds.date.strftime('%Y-%m')):
		grouped_by_month[month] = list(suggestions)

	return render(
		request,
		'daily_suggestions_intro_page.html',
		{
			'today': today,
			'tomorrow': tomorrow,
			'grouped_by_month': grouped_by_month,
			'days_in_month': days_in_month,
		},
	)
