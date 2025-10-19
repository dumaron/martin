import os
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from fpdf import FPDF

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
	daily_suggestion = get_object_or_404(DailySuggestion, date=date)

	# Create PDF
	pdf = FPDF()
	pdf.add_page()

	berkeley_regular = '/Users/duma/Library/Fonts/BerkeleyMono-Regular.otf'
	berkeley_bold = '/Users/duma/Library/Fonts/BerkeleyMono-Bold.otf'

	pdf.add_font('BerkeleyMono', '', berkeley_regular)
	pdf.add_font('BerkeleyMono', 'B', berkeley_bold)

	# Add date as headline
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