from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from core.models import RecurringSuggestion, Task, Project, RecurrenceRule


class DailySuggestionDetailTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='testuser', password='password')
		self.client = Client()
		self.client.force_login(self.user)

		# Project for tasks
		self.project = Project.objects.create(title='Test Project', status='active')

	def test_special_characters_escaping(self):
		# Create a recurring suggestion with special characters
		content_with_special_chars = 'Special chars: > and à'
		# RecurringSuggestion needs a rule or something? Let's check RecurringSuggestion.get_actives_in_date
		# Looking at core/models/recurring_suggestion.py might be good.
		rs = RecurringSuggestion.objects.create(content=content_with_special_chars)
		RecurrenceRule.objects.create(type='daily', day=1, suggestion=rs)
		# Note: I might need to associate it with a rule if get_actives_in_date requires it.

		# Create a task with special characters
		description_with_special_chars = 'Task with > and à'
		Task.objects.create(description=description_with_special_chars, project=self.project, status='pending')

		url = reverse('daily_suggestions_editor_page.main_render', kwargs={'date': date.today().isoformat()})
		response = self.client.get(url)

		self.assertEqual(response.status_code, 200)

		# Print response content to see what's happening
		# print(response.content.decode())

		# With proper HTML escaping (not escapejs), HTML will contain &gt; and preserve à.
		content = response.content.decode()
		self.assertIn('data-suggestion="Special chars: &gt; and à"', content)
		self.assertIn('data-task-description="Task with &gt; and à"', content)
