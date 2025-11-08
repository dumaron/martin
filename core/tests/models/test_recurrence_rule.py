from datetime import date

from django.test import TestCase

from core.models import RecurrenceRule, RecurringSuggestion


class RecurrenceRuleGetActiveInDateTest(TestCase):
	"""Test the get_active_in_date method of RecurrenceRule model."""

	def setUp(self):
		"""Set up test data."""
		# Create a recurring suggestion to use for all tests
		self.suggestion = RecurringSuggestion.objects.create(content='Test suggestion')

	def test_get_active_in_date_returns_daily_recurrence_on_multiple_dates(self):
		"""Test that daily recurrence rules are returned regardless of the date."""
		from datetime import timedelta

		# Create a daily recurrence rule
		daily_rule = RecurrenceRule.objects.create(type='daily', day=0, suggestion=self.suggestion)

		# Test with all days in a leap year
		start_date = date(2024, 1, 1)
		dates_to_test = [
			start_date + timedelta(days=i)
			for i in range(366)  # 2024 is a leap year, so it has 366 days
		]

		for test_date in dates_to_test:
			result = RecurrenceRule.get_active_in_date(test_date)
			self.assertIn(daily_rule, result, f'Daily rule should be returned for {test_date}')

	def test_get_active_in_date_returns_day_of_week_monday(self):
		"""Test that get_active_in_date returns recurrence rules for Monday."""
		# Create a Monday recurrence rule (1 = Monday)
		monday_rule = RecurrenceRule.objects.create(type='day_of_the_week', day=1, suggestion=self.suggestion)

		# Test with a Monday (March 17, 2025 is a Monday)
		monday_date = date(2025, 3, 17)
		result = RecurrenceRule.get_active_in_date(monday_date)

		self.assertIn(monday_rule, result)

	def test_get_active_in_date_does_not_return_wrong_day_of_week(self):
		"""Test that get_active_in_date does not return rules for different days of the week."""
		# Create a Monday recurrence rule (1 = Monday)
		monday_rule = RecurrenceRule.objects.create(type='day_of_the_week', day=1, suggestion=self.suggestion)

		# Test with a Tuesday (March 18, 2025 is a Tuesday)
		tuesday_date = date(2025, 3, 18)
		result = RecurrenceRule.get_active_in_date(tuesday_date)

		self.assertNotIn(monday_rule, result)

	def test_get_active_in_date_returns_day_of_week_sunday(self):
		"""Test that get_active_in_date returns recurrence rules for Sunday."""
		# Create a Sunday recurrence rule (7 = Sunday)
		sunday_rule = RecurrenceRule.objects.create(type='day_of_the_week', day=7, suggestion=self.suggestion)

		# Test with a Sunday (March 16, 2025 is a Sunday)
		sunday_date = date(2025, 3, 16)
		result = RecurrenceRule.get_active_in_date(sunday_date)

		self.assertIn(sunday_rule, result)

	def test_get_active_in_date_does_not_return_day_of_week_sunday(self):
		"""Test that get_active_in_date returns recurrence rules for Sunday."""
		# Create a Sunday recurrence rule (7 = Sunday)
		sunday_rule = RecurrenceRule.objects.create(type='day_of_the_week', day=7, suggestion=self.suggestion)

		# Test with a Sunday (March 17, 2025 is a Monday)
		sunday_date = date(2025, 3, 17)
		result = RecurrenceRule.get_active_in_date(sunday_date)

		self.assertNotIn(sunday_rule, result)

	def test_get_active_in_date_returns_day_of_month(self):
		"""Test that get_active_in_date returns recurrence rules for specific day of the month."""
		# Create a rule for the 15th of each month
		day_15_rule = RecurrenceRule.objects.create(type='day_of_the_month', day=15, suggestion=self.suggestion)

		# Test with March 15, 2025
		march_15 = date(2025, 3, 15)
		result = RecurrenceRule.get_active_in_date(march_15)

		self.assertIn(day_15_rule, result)

		# Test with April 15, 2025 (different month, same day)
		april_15 = date(2025, 4, 15)
		result = RecurrenceRule.get_active_in_date(april_15)

		self.assertIn(day_15_rule, result)

	def test_get_active_in_date_does_not_return_wrong_day_of_month(self):
		"""Test that get_active_in_date does not return rules for different days of the month."""
		# Create a rule for the 15th of each month
		day_15_rule = RecurrenceRule.objects.create(type='day_of_the_month', day=15, suggestion=self.suggestion)

		# Test with March 16, 2025 (wrong day)
		march_16 = date(2025, 3, 16)
		result = RecurrenceRule.get_active_in_date(march_16)

		self.assertNotIn(day_15_rule, result)

	def test_get_active_in_date_returns_first_day_of_week_in_month(self):
		"""Test that get_active_in_date returns rules for first occurrence of a day of week in month."""
		# Create a rule for first Monday of the month (1 = Monday)
		first_monday_rule = RecurrenceRule.objects.create(
			type='first_day_of_week_in_month', day=1, suggestion=self.suggestion
		)

		# Test with the first Monday of March 2025 (March 3, 2025)
		first_monday_march = date(2025, 3, 3)
		result = RecurrenceRule.get_active_in_date(first_monday_march)

		self.assertIn(first_monday_rule, result)

	def test_get_active_in_date_returns_day_of_year_non_leap(self):
		"""Test that get_active_in_date returns recurrence rules for a specific day of the year (non-leap year)."""
		# March 15 in a non-leap year is day 74
		# Create a rule for day 74 of the year
		march_15th_rule = RecurrenceRule.objects.create(type='day_of_the_year', day=74, suggestion=self.suggestion)

		# Test with March 15, 2025 (non-leap year)
		march_15_2025 = date(2025, 3, 15)
		result = RecurrenceRule.get_active_in_date(march_15_2025)

		self.assertIn(march_15th_rule, result)

	def test_get_active_in_date_returns_day_of_year_leap(self):
		"""Test that get_active_in_date correctly handles leap years by adjusting day of year."""
		# March 15 in a non-leap year is day 74
		# In a leap year (2024), March 15 would normally be day 75,
		# but the implementation subtracts 1 for dates after Feb, so it queries for day 74
		leap_march_15th_rule = RecurrenceRule.objects.create(type='day_of_the_year', day=74, suggestion=self.suggestion)

		# Test with March 15, 2024 (leap year)
		march_15_2024 = date(2024, 3, 15)
		result = RecurrenceRule.get_active_in_date(march_15_2024)

		self.assertIn(leap_march_15th_rule, result)

	def test_get_active_in_date_leap_year_before_march(self):
		"""Test that get_active_in_date handles dates before March in leap years without adjustment."""
		# February 10 in any year is day 41 (non-leap) or day 41 (leap)
		# Before March, no adjustment is made
		day_41_rule = RecurrenceRule.objects.create(type='day_of_the_year', day=41, suggestion=self.suggestion)

		# Test with February 10, 2024 (leap year)
		feb_10_2024 = date(2024, 2, 10)
		result = RecurrenceRule.get_active_in_date(feb_10_2024)

		self.assertIn(day_41_rule, result)

	def test_get_active_in_date_does_not_return_first_day_of_week_in_month_for_later_weeks(self):
		"""Test that first_day_of_week_in_month rules do not match when date is not in the first week."""
		# Create a rule for first Monday of the month (1 = Monday)
		first_monday_rule = RecurrenceRule.objects.create(
			type='first_day_of_week_in_month', day=1, suggestion=self.suggestion
		)

		# Test with a Monday in the second week of March 2025 (March 10, 2025 is a Monday, but not in first week)
		second_monday_march = date(2025, 3, 10)
		result = RecurrenceRule.get_active_in_date(second_monday_march)

		self.assertNotIn(first_monday_rule, result)

		# Test with a Monday in the third week (March 17, 2025)
		third_monday_march = date(2025, 3, 17)
		result = RecurrenceRule.get_active_in_date(third_monday_march)

		self.assertNotIn(first_monday_rule, result)

	def test_get_active_in_date_returns_multiple_matching_rules(self):
		"""Test that get_active_in_date returns all matching rules for a given date."""
		# Create multiple rules that could match the same date
		# March 15, 2025 is a Saturday (day 6), day 15 of month, and day 74 of year
		saturday_rule = RecurrenceRule.objects.create(type='day_of_the_week', day=6, suggestion=self.suggestion)
		day_15_rule = RecurrenceRule.objects.create(type='day_of_the_month', day=15, suggestion=self.suggestion)
		day_74_rule = RecurrenceRule.objects.create(type='day_of_the_year', day=74, suggestion=self.suggestion)

		# Create a rule that shouldn't match
		sunday_rule = RecurrenceRule.objects.create(type='day_of_the_week', day=7, suggestion=self.suggestion)

		test_date = date(2025, 3, 15)
		result = RecurrenceRule.get_active_in_date(test_date)

		# Should include all matching rules
		self.assertIn(saturday_rule, result)
		self.assertIn(day_15_rule, result)
		self.assertIn(day_74_rule, result)

		# Should not include non-matching rule
		self.assertNotIn(sunday_rule, result)

	def test_get_active_in_date_with_none_returns_empty(self):
		"""Test that get_active_in_date returns empty list when date is None."""
		# Create some rules
		RecurrenceRule.objects.create(type='daily', day=0, suggestion=self.suggestion)

		result = RecurrenceRule.get_active_in_date(None)

		self.assertEqual(list(result), [])

	def test_get_active_in_date_with_no_matching_rules(self):
		"""Test that get_active_in_date returns empty result when no rules match."""
		# Create a rule for Monday
		RecurrenceRule.objects.create(type='day_of_the_week', day=1, suggestion=self.suggestion)

		# Test with a Saturday
		saturday_date = date(2025, 3, 15)
		result = RecurrenceRule.get_active_in_date(saturday_date)

		self.assertEqual(result.count(), 0)
