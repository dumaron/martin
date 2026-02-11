from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from fpdf import FPDF

from apps.website.pages.page import Page
from core.models import DailySuggestion, RecurringSuggestion, Task
from settings import FONTS_DIR

page = Page(name='daily_suggestions_editor_page', base_route='pages/daily-suggestions/<str:date>')


@page.main
def main_render(request, date):
	date_obj = datetime.strptime(date, '%Y-%m-%d').date()
	today = datetime.now().date()
	is_in_the_past = date_obj < today

	if is_in_the_past:
		daily_suggestion = DailySuggestion.objects.get(date=date)
		active_recurring_suggestions = []
	else:
		try:
			daily_suggestion = DailySuggestion.objects.get(date=date)
		except DailySuggestion.DoesNotExist:
			daily_suggestion = None

		active_recurring_suggestions = RecurringSuggestion.get_actives_in_date(date_obj)

	pending_tasks = Task.objects.filter(
		project__status='active', status__in=['pending', 'active']
	).select_related('project')

	return render(
		request,
		'daily_suggestion_detail/daily_suggestion_detail.html',
		{
			'date': date,
			'daily_suggestion': daily_suggestion,
			'active_recurring_suggestions': active_recurring_suggestions,
			'is_in_the_past': is_in_the_past,
			'pending_tasks': pending_tasks,
		},
	)


@page.action('save')
def save_daily_suggestion(request, date):
	content = request.POST.get('content')
	daily_suggestion, _ = DailySuggestion.objects.get_or_create(date=date)
	daily_suggestion.content = content
	daily_suggestion.save()
	return redirect('daily_suggestions_editor_page.main_render', date=date)


@page.action('pdf', method='GET')
def daily_suggestion_pdf(request, date):
	daily_suggestion = get_object_or_404(DailySuggestion, date=date)

	# Create PDF
	pdf = FPDF()
	pdf.add_page()

	print('FONTS DIR -> ' + FONTS_DIR)

	berkeley_regular = FONTS_DIR + 'BerkeleyMono-Regular.otf'
	berkeley_bold = FONTS_DIR + 'BerkeleyMono-Bold.otf'

	pdf.add_font('BerkeleyMono', '', berkeley_regular)
	pdf.add_font('BerkeleyMono', 'B', berkeley_bold)

	# Add date as a headline
	pdf.set_font('BerkeleyMono', 'B', 16)
	pdf.cell(0, 20, str(date), ln=True, align='L')
	pdf.ln(10)

	# Add daily suggestion content
	pdf.set_font('BerkeleyMono', '', 10)

	if daily_suggestion.content:
		pdf.multi_cell(0, 5, daily_suggestion.content)
	else:
		pdf.multi_cell(0, 5, 'No content available.')

	# Generate PDF output
	pdf_output = bytes(pdf.output())

	# Create HTTP response
	response = HttpResponse(pdf_output, content_type='application/pdf')
	response['Content-Disposition'] = f'attachment; filename="daily_suggestion_{date}.pdf"'

	return response
