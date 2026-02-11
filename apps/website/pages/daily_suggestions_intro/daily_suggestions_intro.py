import calendar
import datetime

from django.shortcuts import render

from apps.website.pages.page import Page
from core.models import DailySuggestion

page = Page(name='daily_suggestions_intro_page', base_route='pages/daily-suggestions')


@page.main
def daily_suggestions_intro_page(request):
	today = datetime.date.today().strftime('%Y-%m-%d')
	tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
	entries = DailySuggestion.objects.order_by('-date').all()
	days_in_month = list(range(1, 32))

	# Create a dictionary based on the previous entries, using the Y-m-d of the date as key
	entries_by_day = {}
	for entry in entries:
		entries_by_day[entry.date.strftime('%Y-%m-%d')] = entry

	entries_months = set(map(lambda ds: ds.date.strftime('%Y-%m'), entries))

	previous_entries_matrix = []
	for month in entries_months:
		month_number = int(month.split('-')[1])
		year_number = int(month.split('-')[0])
		row = []
		for day in days_in_month:
			day_string = f'{year_number}-{month_number:02d}-{day:02d}'
			# if the day cannot exist in the month, add None to the row
			if day > calendar.monthrange(year_number, month_number)[1]:
				row.append('INVALID')
			# if the month is the current month, mark as invalid all days from tomorrow to the end of the day
			elif month_number == datetime.date.today().month and day > (datetime.date.today().day + 1):
				row.append('INVALID')
			# now, if the entry is in the dictionary, add it to the row
			else:
				prev_entry = entries_by_day.get(day_string, None)
				if prev_entry:
					row.append(prev_entry)
				else:
					row.append(None)

		previous_entries_matrix.append({'month': month, 'entries': row})

		sorted_entries = reversed(sorted(previous_entries_matrix, key=lambda x: x['month']))

	return render(
		request,
		'daily_suggestions_intro/daily_suggestions_intro.html',
		{
			'today': today,
			'tomorrow': tomorrow,
			'days_in_month': days_in_month,
			'previous_entries_matrix': sorted_entries,
		},
	)
