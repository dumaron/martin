from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from core.hkm.models import Fact, Retraction, Transaction


class EntityListPageTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='testuser', password='password')
		self.client = Client()
		self.client.force_login(self.user)

		self.tx = Transaction.objects.create(applied_at=timezone.now())

	def get_page(self):
		url = reverse('entity_list_page.main_render')
		return self.client.get(url)

	def test_lists_subjects_of_current_facts(self):
		Fact.objects.create(subject='michelangelo', predicate='born-in', object='florence', transaction=self.tx)
		retracted = Fact.objects.create(
			subject='atlantis', predicate='label', object='Atlantis', transaction=self.tx
		)
		Retraction.objects.create(fact=retracted, transaction=self.tx)

		response = self.get_page()
		content = response.content.decode()

		self.assertEqual(response.status_code, 200)
		self.assertIn('michelangelo', content)
		self.assertNotIn('atlantis', content)

	def test_shows_empty_state_when_no_facts(self):
		response = self.get_page()

		self.assertEqual(response.status_code, 200)
		self.assertIn('No entities yet', response.content.decode())
