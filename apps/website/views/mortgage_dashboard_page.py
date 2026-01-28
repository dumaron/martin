import os
from datetime import datetime
from math import ceil

import django_tables2 as tables
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from dotenv import load_dotenv

# Mortgage constants from environment variables
LOAN_AMOUNT = float(os.getenv('MORTGAGE_LOAN_AMOUNT', '180000'))
ANNUAL_RATE = float(os.getenv('MORTGAGE_ANNUAL_RATE', '0.0281'))
YEARS = int(os.getenv('MORTGAGE_YEARS', '30'))
MONTHLY_FEE = float(os.getenv('MORTGAGE_MONTHLY_FEE', '3.5'))
YEARLY_FEE = float(os.getenv('MORTGAGE_YEARLY_FEE', '49'))
START_DATE = datetime(2025, 2, 27)  # 27 Feb 2025


def ceil_50_cent(value):
	"""Round up to nearest 50 cents"""
	return ceil(value * 2) / 2


def calculate_loan_amortization():
	"""Calculate loan amortization schedule"""
	monthly_rate = ANNUAL_RATE / 12
	num_payments = YEARS * 12
	payed_interest = 0
	amortization_plan = []
	total_loan = LOAN_AMOUNT
	remaining_capital = LOAN_AMOUNT

	for month in range(1, num_payments + 1):
		payment_date = START_DATE + relativedelta(months=month - 1)

		monthly_payment = ceil_50_cent(
			total_loan * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
		)
		interest = remaining_capital * monthly_rate
		payed_interest += interest
		principal = monthly_payment - interest
		remaining_capital -= principal
		end_of_year = month % 12 == 0
		fee = MONTHLY_FEE

		if end_of_year:
			fee += YEARLY_FEE

		if remaining_capital <= 0:
			principal -= abs(remaining_capital)
			interest += abs(remaining_capital)
			payed_interest += abs(remaining_capital)
			remaining_capital = 0

		payment_details = {
			'month': month,
			'date': payment_date.strftime('%Y-%m'),
			'payment': round(monthly_payment + fee, 2),
			'principal': round(principal, 2),
			'interest': round(interest, 2),
			'fee': fee,
			'remaining': round(remaining_capital, 2),
			'total_interest': round(payed_interest, 2),
		}

		amortization_plan.append(payment_details)

		if remaining_capital == 0:
			break

	return amortization_plan


class MortgageAmortizationTable(tables.Table):
	month = tables.Column(verbose_name='Month')
	date = tables.Column(verbose_name='Date')
	payment = tables.Column(verbose_name='Payment')
	principal = tables.Column(verbose_name='Principal')
	interest = tables.Column(verbose_name='Interest')
	fee = tables.Column(verbose_name='Fee')
	remaining = tables.Column(verbose_name='Remaining Balance')
	total_interest = tables.Column(verbose_name='Total Interest Paid')

	class Meta:
		template_name = 'django_tables2/table.html'
		attrs = {'class': 'table'}


@login_required
@require_GET
def main_render(request):
	amortization_data = calculate_loan_amortization()

	# Create table without pagination
	table = MortgageAmortizationTable(amortization_data)
	tables.RequestConfig(request, paginate=False).configure(table)

	# Create Plotly chart with dates
	dates = [item['date'] for item in amortization_data]
	remaining_balance = [item['remaining'] for item in amortization_data]
	principal_paid = [LOAN_AMOUNT - item['remaining'] for item in amortization_data]
	interest_paid = [item['total_interest'] for item in amortization_data]

	fig = go.Figure()

	# Add traces with colors matching Martin aesthetic
	fig.add_trace(
		go.Scatter(x=dates, y=remaining_balance, name='Remaining Balance', line=dict(color='#666666', width=2))
	)

	fig.add_trace(
		go.Scatter(x=dates, y=principal_paid, name='Principal Paid', line=dict(color='#1a1a1a', width=2))
	)

	fig.add_trace(
		go.Scatter(x=dates, y=interest_paid, name='Total Interest Paid', line=dict(color='#999999', width=2))
	)

	# Update layout with ggplot2 theme
	fig.update_layout(
		title='Mortgage Amortization Progress',
		xaxis_title='Date',
		yaxis_title='Amount (€)',
		hovermode='x unified',
		template='none',
		height=500,
	)

	chart_html = fig.to_html(include_plotlyjs='cdn', div_id='mortgage-chart')

	# Calculate end date
	end_date = START_DATE + relativedelta(months=len(amortization_data) - 1)

	return render(
		request,
		'mortgage_dashboard.html',
		{
			'table': table,
			'chart_html': chart_html,
			'loan_info': {
				'loan_amount': LOAN_AMOUNT,
				'annual_rate': ANNUAL_RATE * 100,
				'loan_term': YEARS,
				'monthly_fee': MONTHLY_FEE,
				'yearly_fee': YEARLY_FEE,
				'start_date': START_DATE.strftime('%B %Y'),
				'end_date': end_date.strftime('%B %Y'),
			},
		},
	)
