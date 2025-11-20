from datetime import date

from django.test import TestCase

from core.models import RecurrenceRule, RecurringSuggestion


class RecurringSuggestionGetActivesInDateTest(TestCase):
	"""Test the get_actives_in_date method of RecurringSuggestion model."""

	def test_get_actives_in_date_returns_suggestions_with_matching_rules(self):
		"""Test that get_actives_in_date returns only suggestions with recurrence rules matching the date."""
		# Create multiple suggestions with different recurrence rules
		daily_suggestion = RecurringSuggestion.objects.create(content='Daily task')
		RecurrenceRule.objects.create(type='daily', day=0, suggestion=daily_suggestion)

		monday_suggestion = RecurringSuggestion.objects.create(content='Monday task')
		RecurrenceRule.objects.create(type='day_of_the_week', day=1, suggestion=monday_suggestion)

		day_15_suggestion = RecurringSuggestion.objects.create(content='15th of month task')
		RecurrenceRule.objects.create(type='day_of_the_month', day=15, suggestion=day_15_suggestion)

		# Test with a Monday that is NOT the 15th (March 17, 2025 is a Monday)
		monday_date = date(2025, 3, 17)
		result = RecurringSuggestion.get_actives_in_date(monday_date)

		# Should return daily and Monday suggestions, but not the 15th
		self.assertIn(daily_suggestion, result)
		self.assertIn(monday_suggestion, result)
		self.assertNotIn(day_15_suggestion, result)

	def test_get_actives_in_date_returns_suggestion_with_multiple_rules(self):
		"""Test that a suggestion with multiple recurrence rules is returned if ANY rule matches the date."""
		# Create a suggestion with multiple recurrence rules
		multi_rule_suggestion = RecurringSuggestion.objects.create(content='Task with multiple rules')

		# Add a Monday rule (will match our test date)
		RecurrenceRule.objects.create(type='day_of_the_week', day=1, suggestion=multi_rule_suggestion)

		# Add a 15th of month rule (will NOT match our test date)
		RecurrenceRule.objects.create(type='day_of_the_month', day=15, suggestion=multi_rule_suggestion)

		# Create another suggestion that won't match
		no_match_suggestion = RecurringSuggestion.objects.create(content='No match task')
		RecurrenceRule.objects.create(type='day_of_the_week', day=7, suggestion=no_match_suggestion)

		# Test with a Monday that is NOT the 15th (March 17, 2025 is a Monday)
		monday_date = date(2025, 3, 17)
		result = RecurringSuggestion.get_actives_in_date(monday_date)

		# Should return the multi-rule suggestion because at least one rule matches
		self.assertIn(multi_rule_suggestion, result)
		# Should not return the non-matching suggestion
		self.assertNotIn(no_match_suggestion, result)

	def test_get_actives_in_date_returns_empty_when_no_rules_match(self):
		"""Test that get_actives_in_date returns empty queryset when no recurrence rules match the date."""
		# Create suggestions with rules that won't match our test date
		tuesday_suggestion = RecurringSuggestion.objects.create(content='Tuesday task')
		RecurrenceRule.objects.create(type='day_of_the_week', day=2, suggestion=tuesday_suggestion)

		day_20_suggestion = RecurringSuggestion.objects.create(content='20th of month task')
		RecurrenceRule.objects.create(type='day_of_the_month', day=20, suggestion=day_20_suggestion)

		# Test with Monday the 17th (March 17, 2025)
		monday_17th = date(2025, 3, 17)
		result = RecurringSuggestion.get_actives_in_date(monday_17th)

		# Should return no suggestions
		self.assertEqual(result.count(), 0)
		self.assertNotIn(tuesday_suggestion, result)
		self.assertNotIn(day_20_suggestion, result)
