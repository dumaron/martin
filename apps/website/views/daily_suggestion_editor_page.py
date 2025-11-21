from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from fpdf import FPDF

from core.models import DailySuggestion, RecurringSuggestion


@login_required
@require_GET
def daily_suggestions_editor_page(request, date):
	daily_suggestion, _ = DailySuggestion.objects.get_or_create(date=date)
	date_obj = datetime.strptime(date, '%Y-%m-%d').date()
	active_recurring_suggestions = RecurringSuggestion.get_actives_in_date(date_obj)
	return render(request, 'daily_suggestions_editor_page.html', {
		'daily_suggestion': daily_suggestion,
		'active_recurring_suggestions': active_recurring_suggestions
	})


@login_required
@require_POST
def save_daily_suggestion(request, date):
	content = request.POST.get('content')
	daily_suggestion, _ = DailySuggestion.objects.get_or_create(date=date)
	daily_suggestion.content = content
	daily_suggestion.save()
	return redirect('daily_suggestions_editor_page', date=date)


@login_required
def add_recurrent_suggestion_to_daily_suggestion(request, date, suggestion_id):
	daily_suggestion = get_object_or_404(DailySuggestion, date=date)
	suggestion = get_object_or_404(RecurringSuggestion, id=suggestion_id)
	daily_suggestion.content += f'\n[ ] {suggestion.content}'
	daily_suggestion.save()
	return redirect('daily_suggestions_editor_page', date=date)


@login_required
@require_GET
def daily_suggestion_pdf(request, date):
	daily_suggestion = get_object_or_404(DailySuggestion, date=date)

	# Create PDF
	pdf = FPDF()
	pdf.add_page()

	# berkeley_regular = '/Users/duma/Library/Fonts/BerkeleyMono-Regular.otf'
	# berkeley_bold = '/Users/duma/Library/Fonts/BerkeleyMono-Bold.otf'

	# pdf.add_font('BerkeleyMono', '', berkeley_regular)
	# pdf.add_font('BerkeleyMono', 'B', berkeley_bold)

	# Add date as a headline
	pdf.set_font('Times', 'B', 16)
	pdf.cell(0, 20, str(date), ln=True, align='L')
	pdf.ln(10)

	# Add daily suggestion content
	pdf.set_font('Times', '', 10)

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
