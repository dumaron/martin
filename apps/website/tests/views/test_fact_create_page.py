from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from core import hkm
from core.hkm.models import Fact, Transaction
from core.utils.fp import lmap


def _formset_data(rows, **extra):
	data = {
		'form-TOTAL_FORMS': str(len(rows)),
		'form-INITIAL_FORMS': '0',
		'form-MIN_NUM_FORMS': '0',
		'form-MAX_NUM_FORMS': '1000',
	}
	for index, (subject, predicate, value) in enumerate(rows):
		data[f'form-{index}-subject'] = subject
		data[f'form-{index}-predicate'] = predicate
		data[f'form-{index}-object'] = value
	data.update(extra)
	return data


def _staged_triples(transaction):
	return lmap(lambda fact: (fact.subject, fact.predicate, fact.object), transaction.facts.order_by('id'))


class FactCreatePageTestCase(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='testuser', password='password')
		self.client = Client()
		self.client.force_login(self.user)

	def _review_url(self, transaction):
		return reverse('fact_review_page.main_render', kwargs={'transaction_id': transaction.id})


class PendingDraftsSectionTest(FactCreatePageTestCase):
	def get_page(self):
		return self.client.get(reverse('fact_create_page.main_render'))

	def test_lists_pending_drafts_with_links_to_their_review_pages(self):
		draft = hkm.create_draft_transaction([('rome', 'is-capital-of', 'italy')], description='capitals')

		content = self.get_page().content.decode()

		self.assertIn('Pending drafts', content)
		self.assertIn('capitals', content)
		self.assertIn(self._review_url(draft), content)

	def test_falls_back_to_the_draft_id_when_there_is_no_description(self):
		draft = hkm.create_draft_transaction([('rome', 'is-capital-of', 'italy')])

		self.assertIn(f'Draft #{draft.id}', self.get_page().content.decode())

	def test_hides_the_section_when_there_are_no_drafts(self):
		self.assertNotIn('Pending drafts', self.get_page().content.decode())

	def test_ignores_applied_transactions(self):
		draft = hkm.create_draft_transaction([('rome', 'is-capital-of', 'italy')], description='capitals')
		hkm.apply_transaction(draft)

		self.assertNotIn('Pending drafts', self.get_page().content.decode())


class CreateFactsTest(FactCreatePageTestCase):
	def post_save(self, data):
		return self.client.post(reverse('fact_create_page.actions.create_facts'), data)

	def test_valid_submission_creates_a_draft_and_redirects_to_review(self):
		response = self.post_save(_formset_data([('rome', 'is-capital-of', 'italy')], description='capitals'))

		draft = Transaction.objects.get()
		self.assertIsNone(draft.applied_at)
		self.assertEqual(draft.description, 'capitals')
		self.assertEqual(_staged_triples(draft), [('rome', 'is-capital-of', 'italy')])
		self.assertRedirects(response, self._review_url(draft))

	def test_blank_rows_are_skipped(self):
		response = self.post_save(_formset_data([('rome', 'is-capital-of', 'italy'), ('', '', '')]))

		draft = Transaction.objects.get()
		self.assertEqual(_staged_triples(draft), [('rome', 'is-capital-of', 'italy')])
		self.assertRedirects(response, self._review_url(draft))

	def test_half_filled_row_is_rejected(self):
		response = self.post_save(_formset_data([('rome', '', '')]))

		self.assertEqual(response.status_code, 200)
		self.assertFalse(Transaction.objects.exists())

	def test_empty_submission_re_renders_with_an_error(self):
		response = self.post_save(_formset_data([('', '', '')]))

		self.assertEqual(response.status_code, 200)
		self.assertIn('Add at least one fact or retraction', response.content.decode())
		self.assertFalse(Transaction.objects.exists())


class EditDraftPageTest(FactCreatePageTestCase):
	def setUp(self):
		super().setUp()
		applied = Transaction.objects.create(applied_at=timezone.now())
		self.current = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=applied
		)
		self.draft = hkm.create_draft_transaction(
			[('jhon-doe', 'works-at', 'acme')], retractions=[self.current.id], description='people'
		)

	def get_page(self, transaction):
		return self.client.get(
			reverse('fact_create_page.actions.edit_draft', kwargs={'transaction_id': transaction.id})
		)

	def test_prefills_the_staged_facts_even_when_not_known_entities(self):
		# 'jhon-doe' only exists in the draft, so it is absent from the known-entities options and must be
		# injected as a selected option for the prefill to survive rendering.
		content = self.get_page(self.draft).content.decode()

		self.assertIn('Edit draft', content)
		self.assertIn('<option value="jhon-doe" selected>jhon-doe</option>', content)
		self.assertIn('people', content)

	def test_marks_staged_retractions_as_selected(self):
		content = self.get_page(self.draft).content.decode()

		self.assertIn(f'<option value="{self.current.id}" selected>', content)

	def test_form_posts_to_the_update_action(self):
		content = self.get_page(self.draft).content.decode()

		update_url = reverse('fact_create_page.actions.update_facts', kwargs={'transaction_id': self.draft.id})
		self.assertIn(f'action="{update_url}"', content)

	def test_applied_transaction_redirects_to_review(self):
		hkm.apply_transaction(self.draft)

		response = self.get_page(self.draft)

		self.assertRedirects(response, self._review_url(self.draft))


class UpdateFactsTest(FactCreatePageTestCase):
	def setUp(self):
		super().setUp()
		applied = Transaction.objects.create(applied_at=timezone.now())
		self.current = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=applied
		)
		self.draft = hkm.create_draft_transaction(
			[('jhon-doe', 'works-at', 'acme')], retractions=[self.current.id], description='people'
		)

	def post_update(self, data):
		return self.client.post(
			reverse('fact_create_page.actions.update_facts', kwargs={'transaction_id': self.draft.id}), data
		)

	def test_replaces_the_staged_facts_and_redirects_to_review(self):
		response = self.post_update(_formset_data([('john-doe', 'works-at', 'acme')], description='fixed'))

		self.draft.refresh_from_db()
		self.assertEqual(_staged_triples(self.draft), [('john-doe', 'works-at', 'acme')])
		self.assertEqual(self.draft.description, 'fixed')
		# The same draft was updated in place — no second transaction appeared.
		self.assertEqual(Transaction.objects.filter(applied_at=None).count(), 1)
		self.assertRedirects(response, self._review_url(self.draft))

	def test_keeps_a_retraction_staged_by_the_draft_itself(self):
		data = _formset_data([('john-doe', 'works-at', 'acme')], retractions=[str(self.current.id)])

		self.post_update(data)

		self.assertEqual(list(self.draft.retractions.values_list('fact_id', flat=True)), [self.current.id])

	def test_drops_a_deselected_retraction(self):
		self.post_update(_formset_data([('john-doe', 'works-at', 'acme')]))

		self.assertFalse(self.draft.retractions.exists())

	def test_blanked_rows_are_dropped_from_the_draft(self):
		hkm.update_draft(self.draft, [('jhon-doe', 'works-at', 'acme'), ('rome', 'founded-in', '-753')])

		self.post_update(_formset_data([('', '', ''), ('rome', 'founded-in', '-753')]))

		self.assertEqual(_staged_triples(self.draft), [('rome', 'founded-in', '-753')])

	def test_empty_update_re_renders_with_an_error_and_keeps_the_draft(self):
		response = self.post_update(_formset_data([('', '', '')]))

		self.assertEqual(response.status_code, 200)
		self.assertIn('Add at least one fact or retraction', response.content.decode())
		self.assertEqual(_staged_triples(self.draft), [('jhon-doe', 'works-at', 'acme')])

	def test_applied_transaction_is_left_untouched(self):
		hkm.apply_transaction(self.draft)

		response = self.post_update(_formset_data([('john-doe', 'works-at', 'acme')]))

		self.assertRedirects(response, self._review_url(self.draft))
		self.assertEqual(_staged_triples(self.draft), [('jhon-doe', 'works-at', 'acme')])
