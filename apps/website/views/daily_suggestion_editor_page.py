from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.models import DailySuggestion


@login_required
@require_GET
def daily_suggestions_editor_page(request, date):
	daily_suggestion = DailySuggestion.get_or_create(date)
	return render(request, 'daily_suggestions_editor_page.html', {'daily_suggestion': daily_suggestion})


@login_required
@require_POST
def save_daily_suggestion(request, date):
	content = request.POST.get('content')
	daily_suggestion = DailySuggestion.get_or_create(date)
	daily_suggestion.content = content
	daily_suggestion.save()
	return redirect('daily_suggestions_editor_page', date=date)


@login_required
@require_GET
def daily_suggestion_pdf(request, date):
	pass