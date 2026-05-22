from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import render

from apps.website.pages.monthly_report.report_renderer import render_report_pdf
from apps.website.pages.page import Page
from core.models import BankTransaction

import calendar


page = Page(name='monthly_report_page', base_route='pages/finances/monthly-report')


@page.main
def main_render(request):
	# For Claude: if a similar query gets duplicated elsewhere, consider solutions for centralization
	bank_transactions_months = (
		BankTransaction.objects.filter(
			bank_account__personal=False,
			matched_ynab_transaction__isnull=False,
			matched_ynab_transaction__transfer_account_id__isnull=True,
			amount__lt=0,
		)
		.annotate(month_start=TruncMonth('date'))
		.values_list('month_start', flat=True)
		.distinct()
		.order_by('-month_start')
	)

	months = list(
		map(
			lambda m: {'year': m.year, 'month': m.month, 'label': f'{calendar.month_name[m.month]} {m.year}'},
			bank_transactions_months,
		)
	)

	return render(request, 'monthly_report/monthly_report.html', {'months': months})


@page.action('pdf/<int:year>/<int:month>', method='GET')
def download_pdf(request, year, month):
	pdf_bytes = render_report_pdf(year, month)
	filename = f'monthly-report-{year:04d}-{month:02d}.pdf'
	response = HttpResponse(pdf_bytes, content_type='application/pdf')
	response['Content-Disposition'] = f'inline; filename="{filename}"'
	return response
