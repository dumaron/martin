import calendar
from functools import reduce
from operator import or_

from django.db import models
from django.db.models import Q

# ICal-based recurrencies looked too complex for my use-case: a lot of scenarios are covered, but it would have
# required me to install a dependency, and it seems it's hard to query for entries that are active within a specific
# date. Then I read stuff about caching and pre-calculating... oh boy.
#
# This complexity is overkill for my use case, and if I can avoid relying on another dependency, I'd be happy.
# So I came up with this simple implementation of recurring events. This is probably too naive, but... who cares, I'm
# here to learn too.

class RecurrenceRule(models.Model):

	class Meta:
		db_table = 'recurrence_rules'

	RECURRENCE_TYPES =  [
		# For daily tasks, like "clean the cat's litter box"
		('daily', 'Daily'),
		# For weekly tasks, like "call mom every Friday afternoon"
		('day_of_the_week', 'Day of the week'),
		# For monthly tasks, like "pay the rent on the 15th of each month"
		('day_of_the_month', 'Day of the month'),
		# For monthly tasks that happens in specific days after a month starts,
		# like "check finances and refresh budget trajectory every first Sunday of the month"
		('first_day_of_week_in_month', 'First day of the week in the month'),
		# For yearly tasks, like "send a lovely message to your wife for your wedding anniversary"
		# Remember: at the end, Martin is a creation of love, made to help me give people the care and attention they
		# deserve.
		('day_of_the_year', 'Day of the year'),
	]
	type = models.CharField(max_length=26, choices=RECURRENCE_TYPES, default='daily')

	# The "day" is an integer number that should be interpreted according to the recurrence type:
	# - daily                        -> not used
	# - day_of_the_week              -> 1 = Monday, 7 = Sunday
	# - day_of_the_month             -> the specific day of the month, with the exception that -1 means "last day of the month"
	# - first_day_of_week_in_month   -> like day_of_the_week, but means something like "first Monday of the month"
	# - day_of_the_year              -> specific day of the year, with the caveat that Feb's 29th is not supported
	#
	# Lap years are not supported by design, we will consider as if 29th of February doesn't exist (rude).
	day = models.IntegerField()

	suggestion = models.ForeignKey('RecurringSuggestion', on_delete=models.PROTECT)

	@classmethod
	def get_active_in_date(cls, date):
		if not date:
			return []

		day_of_week = date.isoweekday()
		day_of_month = date.day
		year_is_leap = calendar.isleap(date.year)
		day_of_year = date.timetuple().tm_yday
		is_after_february = date.month >= 3
		if year_is_leap and is_after_february:
			day_of_year -= 1
		is_first_week_of_month = day_of_month <= 7

		q_objects = [
			Q(type='daily'),
			Q(type='day_of_the_week', day=day_of_week),
			Q(type='day_of_the_month', day=day_of_month),
			Q(type='day_of_the_year', day=day_of_year),
		]

		if is_first_week_of_month:
			q_objects.append(Q(type='first_day_of_week_in_month', day=day_of_week))

		return cls.objects.filter(reduce(or_, q_objects))
