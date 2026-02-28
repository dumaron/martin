from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from core.models import Project, Task


class ProjectsPageTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='testuser', password='password')
		self.client = Client()
		self.client.force_login(self.user)

		self.active_project = Project.objects.create(title='Active Project', status='active')
		self.pending_project = Project.objects.create(title='Pending Project', status='pending')
		self.completed_project = Project.objects.create(title='Completed Project', status='completed')
		self.archived_project = Project.objects.create(title='Archived Project', status='archived')

	def get_page(self):
		url = reverse('projects_page.main_render')
		return self.client.get(url)

	def test_shows_only_active_root_projects(self):
		response = self.get_page()
		content = response.content.decode()

		self.assertEqual(response.status_code, 200)
		self.assertIn('Active Project', content)
		self.assertNotIn('Pending Project', content)
		self.assertNotIn('Completed Project', content)
		self.assertNotIn('Archived Project', content)

	def test_shows_only_active_and_pending_tasks_for_project(self):
		Task.objects.create(description='Active task', project=self.active_project, status='active')
		Task.objects.create(description='Pending task', project=self.active_project, status='pending')
		Task.objects.create(description='Completed task', project=self.active_project, status='completed')
		Task.objects.create(description='Aborted task', project=self.active_project, status='aborted')

		response = self.get_page()
		content = response.content.decode()

		self.assertIn('Active task', content)
		self.assertIn('Pending task', content)
		self.assertNotIn('Completed task', content)
		self.assertNotIn('Aborted task', content)

	def test_shows_only_active_and_pending_orphan_tasks(self):
		Task.objects.create(description='Active orphan', project=None, status='active')
		Task.objects.create(description='Pending orphan', project=None, status='pending')
		Task.objects.create(description='Completed orphan', project=None, status='completed')
		Task.objects.create(description='Aborted orphan', project=None, status='aborted')

		response = self.get_page()
		content = response.content.decode()

		self.assertIn('Active orphan', content)
		self.assertIn('Pending orphan', content)
		self.assertNotIn('Completed orphan', content)
		self.assertNotIn('Aborted orphan', content)
