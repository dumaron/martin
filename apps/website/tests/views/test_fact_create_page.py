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
		return self.client.get(reverse('knowledge_transaction_upsert_page.main_render'))

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

	def test_uses_datalist_inputs_for_fact_fields(self):
		content = self.get_page().content.decode()

		self.assertIn('<datalist id="hkm-entity-options">', content)
		self.assertIn('<datalist id="hkm-predicate-options">', content)
		self.assertRegex(content, r'<input[^>]+name="form-0-subject"[^>]+list="hkm-entity-options"')
		self.assertRegex(content, r'<input[^>]+name="form-0-predicate"[^>]+list="hkm-predicate-options"')
		self.assertRegex(content, r'<input[^>]+name="form-0-object"[^>]+list="hkm-entity-options"')
		self.assertNotIn('class="tom-select"', content)

	def test_asks_the_server_for_extra_fact_rows(self):
		# Rows come from the fact-row partial, which needs to be told how many the form already has.
		content = self.get_page().content.decode()

		self.assertRegex(
			content,
			r'id="add-fact"\s+hx-get="{}"\s+hx-include="#id_form-TOTAL_FORMS"'.format(
				reverse('knowledge_transaction_upsert_page.partials.fact_row')
			),
		)
		# No client-side row cloning left over.
		self.assertNotIn('empty-fact-row', content)
		self.assertNotIn('__prefix__', content)
		# The rows here come from the formset, which writes the management form itself: the row template's
		# out-of-band counter belongs to the HTMX response alone.
		self.assertNotIn('hx-swap-oob', content)


class CreateFactsTest(FactCreatePageTestCase):
	def post_save(self, data):
		return self.client.post(reverse('knowledge_transaction_upsert_page.actions.save_hkm_transaction'), data)

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


class AddFactRowPartialTest(FactCreatePageTestCase):
	def get_row(self, **params):
		return self.client.get(reverse('knowledge_transaction_upsert_page.partials.fact_row'), params)

	def test_renders_the_row_the_reported_count_names(self):
		content = self.get_row(**{'form-TOTAL_FORMS': '2'}).content.decode()

		self.assertRegex(content, r'<input[^>]+name="form-2-subject"[^>]+list="hkm-entity-options"')
		self.assertRegex(content, r'<input[^>]+name="form-2-predicate"[^>]+list="hkm-predicate-options"')
		self.assertRegex(content, r'<input[^>]+name="form-2-object"[^>]+list="hkm-entity-options"')

	def test_swaps_the_incremented_row_count_back(self):
		content = self.get_row(**{'form-TOTAL_FORMS': '2'}).content.decode()

		self.assertRegex(
			content,
			r'<input type="hidden" name="form-TOTAL_FORMS"[^>]+id="id_form-TOTAL_FORMS"'
			r'[^>]+value="3" hx-swap-oob="true">',
		)

	def test_falls_back_to_the_first_row_when_the_count_is_unusable(self):
		for params in ({}, {'form-TOTAL_FORMS': ''}, {'form-TOTAL_FORMS': 'two'}):
			with self.subTest(params=params):
				content = self.get_row(**params).content.decode()

				self.assertIn('name="form-0-subject"', content)
				self.assertRegex(content, r'name="form-TOTAL_FORMS"[^>]+value="1"')

	def test_the_row_may_be_left_blank(self):
		# An unused extra row is dropped on save rather than rejected, so it must not be required in the browser
		# either — which is also what the formset does for the rows it renders itself.
		self.assertNotIn('required', self.get_row(**{'form-TOTAL_FORMS': '1'}).content.decode())

	def test_a_row_added_this_way_is_bound_on_save(self):
		row = self.get_row(**{'form-TOTAL_FORMS': '1'}).content.decode()
		self.assertIn('name="form-1-subject"', row)

		self.client.post(
			reverse('knowledge_transaction_upsert_page.actions.save_hkm_transaction'),
			_formset_data([('rome', 'is-capital-of', 'italy'), ('paris', 'is-capital-of', 'france')]),
		)

		self.assertEqual(
			_staged_triples(Transaction.objects.get()),
			[('rome', 'is-capital-of', 'italy'), ('paris', 'is-capital-of', 'france')],
		)


class RetractionRowPartialTest(FactCreatePageTestCase):
	def setUp(self):
		super().setUp()
		applied = Transaction.objects.create(applied_at=timezone.now())
		self.rome = Fact.objects.create(
			subject='rome', predicate='is-capital-of', object='france', transaction=applied
		)
		self.paris = Fact.objects.create(
			subject='paris', predicate='is-capital-of', object='france', transaction=applied
		)

	def option_value(self, fact):
		# Exactly what the datalist offers for that fact — the id is what the server reads back out of it.
		return f'{fact.id}: {fact.subject} — {fact.predicate} — {fact.object}'

	def get_row(self, **params):
		return self.client.get(reverse('knowledge_transaction_upsert_page.partials.retraction_row'), params)

	def test_renders_the_row_for_the_fact_the_search_value_names(self):
		response = self.get_row(retraction_query=self.option_value(self.rome))

		content = response.content.decode()
		self.assertEqual(response.status_code, 200)
		self.assertIn(f'<span>{self.rome.subject} — {self.rome.predicate} — {self.rome.object}</span>', content)
		self.assertIn(f'name="retractions" value="{self.rome.id}"', content)

	def test_answers_no_content_when_the_search_matches_nothing(self):
		for query in ('', 'rom', 'not-an-id', str(self.rome.id + 1000)):
			with self.subTest(query=query):
				self.assertEqual(self.get_row(retraction_query=query).status_code, 204)

	def test_answers_no_content_when_the_fact_is_already_selected(self):
		# What keeps a search committed twice — the field changing and the button being clicked — from adding
		# the same fact twice.
		response = self.get_row(
			retraction_query=self.option_value(self.rome), retractions=[str(self.rome.id), str(self.paris.id)]
		)

		self.assertEqual(response.status_code, 204)

	def test_a_fact_held_for_another_one_is_still_added(self):
		response = self.get_row(retraction_query=self.option_value(self.rome), retractions=[str(self.paris.id)])

		self.assertEqual(response.status_code, 200)
		self.assertIn(f'name="retractions" value="{self.rome.id}"', response.content.decode())

	def test_a_fact_a_draft_has_staged_for_retraction_is_still_offered(self):
		# A staged retraction has removed nothing yet, so the fact stays current and stays pickable — including
		# by the draft that staged it, which is how reopening that draft shows its own selection back.
		hkm.create_draft_transaction([('jhon-doe', 'works-at', 'acme')], retractions=[self.rome.id])

		self.assertEqual(self.get_row(retraction_query=self.option_value(self.rome)).status_code, 200)

	def test_a_fact_an_applied_retraction_has_removed_is_gone(self):
		draft = hkm.create_draft_transaction([], retractions=[self.rome.id])
		hkm.apply_transaction(draft)

		self.assertEqual(self.get_row(retraction_query=self.option_value(self.rome)).status_code, 204)


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
		return self.client.get(reverse('knowledge_transaction_upsert_page.main_render', kwargs={'transaction_id': transaction.id}))

	def test_prefills_the_staged_facts_even_when_not_known_entities(self):
		# 'jhon-doe' only exists in the draft, so it is absent from the known-entities suggestions. A datalist
		# backed text input must still preserve it as the current value.
		content = self.get_page(self.draft).content.decode()

		self.assertIn('Edit draft', content)
		self.assertIn('value="jhon-doe"', content)
		self.assertIn('people', content)

	def test_marks_staged_retractions_as_selected(self):
		content = self.get_page(self.draft).content.decode()

		self.assertIn(f'name="retractions" value="{self.current.id}"', content)

	def test_the_picker_points_at_the_retraction_row_partial(self):
		content = self.get_page(self.draft).content.decode()

		self.assertIn(f'hx-get="{reverse("knowledge_transaction_upsert_page.partials.retraction_row")}"', content)
		# No client-side selection bookkeeping left over.
		self.assertNotIn('data-remove-retraction', content)
		self.assertNotIn('data-retraction-id', content)

	def test_form_posts_to_the_update_action(self):
		content = self.get_page(self.draft).content.decode()

		update_url = reverse(
			'knowledge_transaction_upsert_page.actions.save_hkm_transaction', kwargs={'transaction_id': self.draft.id}
		)
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
			reverse('knowledge_transaction_upsert_page.actions.save_hkm_transaction', kwargs={'transaction_id': self.draft.id}),
			data,
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
