from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import DailySuggestion, RecurrenceRule, RecurringSuggestion

PAST_DATE = '2020-01-15'
UPCOMING_DATE = '2099-01-15'
MALFORMED_DATE = 'not-a-date'
IMPOSSIBLE_DATE = '2026-02-30'


class MainRenderTest(TestCase):
	def setUp(self):
		self.client.force_login(User.objects.create_user(username='tester'))

	def url(self, date: str) -> str:
		return reverse('daily_suggestions_editor_page.main_render', kwargs={'date': date})

	def test_shows_saved_suggestion(self):
		"""Opening a date that has a saved suggestion renders the page with that suggestion's content."""
		daily_suggestion = DailySuggestion.objects.create(date=date(2099, 1, 15), content='Water the plants')

		response = self.client.get(self.url(UPCOMING_DATE))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['daily_suggestion'], daily_suggestion)
		self.assertContains(response, 'Water the plants')

	def test_upcoming_date_lists_recurring_suggestions(self):
		"""Opening an upcoming date lists the recurring suggestions that are active on that date."""
		recurring_suggestion = RecurringSuggestion.objects.create(content='Take out the trash')
		RecurrenceRule.objects.create(type='daily', day=0, suggestion=recurring_suggestion)

		response = self.client.get(self.url(UPCOMING_DATE))

		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.context['is_in_the_past'])
		self.assertIn(recurring_suggestion, response.context['active_recurring_suggestions'])

	def test_past_date_without_suggestion(self):
		"""Opening a past date that has no saved suggestion renders the page with no suggestion and no recurring ones."""
		recurring_suggestion = RecurringSuggestion.objects.create(content='Take out the trash')
		RecurrenceRule.objects.create(type='daily', day=0, suggestion=recurring_suggestion)

		response = self.client.get(self.url(PAST_DATE))

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.context['is_in_the_past'])
		self.assertIsNone(response.context['daily_suggestion'])
		self.assertEqual(response.context['active_recurring_suggestions'], [])

	def test_malformed_date(self):
		"""Opening a date that is not written as YYYY-MM-DD answers 400."""
		response = self.client.get(self.url(MALFORMED_DATE))

		self.assertEqual(response.status_code, 400)

	def test_impossible_date(self):
		"""Opening a date that is written as YYYY-MM-DD but does not exist in the calendar answers 400."""
		response = self.client.get(self.url(IMPOSSIBLE_DATE))

		self.assertEqual(response.status_code, 400)


class SaveDailySuggestionTest(TestCase):
	def setUp(self):
		self.client.force_login(User.objects.create_user(username='tester'))

	def url(self, date: str) -> str:
		return reverse('daily_suggestions_editor_page.actions.save_daily_suggestion', kwargs={'date': date})

	def test_creates_suggestion(self):
		"""Saving content for a date with no suggestion creates it and goes back to the page of that date."""
		response = self.client.post(self.url(UPCOMING_DATE), {'content': 'Water the plants'})

		self.assertEqual(DailySuggestion.objects.get(date=date(2099, 1, 15)).content, 'Water the plants')
		self.assertRedirects(
			response,
			reverse('daily_suggestions_editor_page.main_render', kwargs={'date': UPCOMING_DATE}),
			fetch_redirect_response=False,
		)

	def test_updates_existing_suggestion(self):
		"""Saving content for a date that already has a suggestion replaces its content without adding a second one."""
		DailySuggestion.objects.create(date=date(2099, 1, 15), content='Water the plants')

		self.client.post(self.url(UPCOMING_DATE), {'content': 'Call the plumber'})

		self.assertEqual(DailySuggestion.objects.get(date=date(2099, 1, 15)).content, 'Call the plumber')
		self.assertEqual(DailySuggestion.objects.count(), 1)

	def test_malformed_date(self):
		"""Saving content for a date that is not written as YYYY-MM-DD answers 400 and saves nothing."""
		response = self.client.post(self.url(MALFORMED_DATE), {'content': 'Water the plants'})

		self.assertEqual(response.status_code, 400)
		self.assertEqual(DailySuggestion.objects.count(), 0)

	def test_impossible_date(self):
		"""Saving content for a date that does not exist in the calendar answers 400 and saves nothing."""
		response = self.client.post(self.url(IMPOSSIBLE_DATE), {'content': 'Water the plants'})

		self.assertEqual(response.status_code, 400)
		self.assertEqual(DailySuggestion.objects.count(), 0)


class DailySuggestionPdfTest(TestCase):
	def setUp(self):
		self.client.force_login(User.objects.create_user(username='tester'))

	def url(self, date: str) -> str:
		return reverse('daily_suggestions_editor_page.actions.daily_suggestion_pdf', kwargs={'date': date})

	def test_date_without_suggestion(self):
		"""Downloading the PDF of a date that has no saved suggestion answers 404."""
		response = self.client.get(self.url(UPCOMING_DATE))

		self.assertEqual(response.status_code, 404)

	def test_malformed_date(self):
		"""Downloading the PDF of a date that is not written as YYYY-MM-DD answers 400."""
		response = self.client.get(self.url(MALFORMED_DATE))

		self.assertEqual(response.status_code, 400)

	def test_impossible_date(self):
		"""Downloading the PDF of a date that does not exist in the calendar answers 400."""
		response = self.client.get(self.url(IMPOSSIBLE_DATE))

		self.assertEqual(response.status_code, 400)
