from django.http import HttpResponse
from django.shortcuts import render

from apps.website.pages.monthly_report.typst_renderer import render_report_pdf
from apps.website.pages.page import Page
from core.reports.monthly_expense_report import build_monthly_expense_report, list_available_months

MONTH_NAMES = (
	'',
	'January',
	'February',
	'March',
	'April',
	'May',
	'June',
	'July',
	'August',
	'September',
	'October',
	'November',
	'December',
)


page = Page(name='monthly_report_page', base_route='pages/finances/monthly-report')


@page.main
def main_render(request):
	months = [
		{'year': year, 'month': month, 'label': f'{MONTH_NAMES[month]} {year}'}
		for year, month in list_available_months()
	]
	return render(request, 'monthly_report/monthly_report.html', {'months': months})


@page.action('pdf/<int:year>/<int:month>', method='GET')
def download_pdf(request, year, month):
	report = build_monthly_expense_report(year, month)
	pdf_bytes = render_report_pdf(report)
	filename = f'monthly-report-{year:04d}-{month:02d}.pdf'
	response = HttpResponse(pdf_bytes, content_type='application/pdf')
	response['Content-Disposition'] = f'inline; filename="{filename}"'
	return response
