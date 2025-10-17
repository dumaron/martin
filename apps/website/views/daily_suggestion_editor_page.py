import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.models import DailySuggestion


@login_required
@require_GET
def daily_suggestions_intro_page(request):

	today = datetime.date.today().strftime('%Y-%m-%d')
	tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

	return render(request, 'daily_suggestions_intro_page.html', {'today': today, 'tomorrow': tomorrow})


@login_required
@require_GET
def daily_suggestions_editor_page(request, date):
	daily_suggestion = DailySuggestion.get_or_create(date)
	return render(request, 'daily_suggestions_editor_page.html', {'daily_suggestion': daily_suggestion})
