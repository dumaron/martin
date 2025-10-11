from datetime import date, datetime
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from core.models import Memory


class MemorySelectMemoryForTodayTest(TestCase):
	"""Test the select_memory_for_today static method of Memory model."""

	def setUp(self):
		"""Set up test data."""
		# Create test photo files
		self.test_photo1 = SimpleUploadedFile('photo1.jpg', b'photo1 content', content_type='image/jpeg')
		self.test_photo2 = SimpleUploadedFile('photo2.jpg', b'photo2 content', content_type='image/jpeg')
		self.test_photo3 = SimpleUploadedFile('photo3.jpg', b'photo3 content', content_type='image/jpeg')

	def test_select_memory_for_today_returns_already_selected_memory(self):
		"""Test that select_memory_for_today returns a memory already selected for today."""
		today = date.today()

		# Create a memory that was already selected today
		memory1 = Memory.objects.create(
			photo=self.test_photo1, description='Memory already selected today', last_selected_on=today
		)

		# Create another memory not selected today
		Memory.objects.create(
			photo=self.test_photo2, description='Memory not selected today', last_selected_on=date(2024, 1, 1)
		)

		with patch('core.models.memory.datetime') as mock_datetime:
			mock_datetime.today.return_value = datetime.combine(today, datetime.min.time())

			result = Memory.select_memory_for_today()

		self.assertEqual(result, memory1)
		# Verify last_selected_on wasn't changed
		memory1.refresh_from_db()
		self.assertEqual(memory1.last_selected_on, today)

	def test_select_memory_for_today_selects_and_updates_memory(self):
		"""Test that select_memory_for_today selects a memory and updates last_selected_on."""
		today = date.today()

		# Create memories with different selection dates
		memory1 = Memory.objects.create(
			photo=self.test_photo1, description='Oldest memory', last_selected_on=date(2024, 1, 1)
		)

		Memory.objects.create(
			photo=self.test_photo2, description='Recent memory', last_selected_on=date(2024, 6, 1)
		)

		with (
			patch('core.models.memory.datetime') as mock_datetime,
			patch('core.models.memory.random.choice') as mock_choice,
		):
			mock_datetime.today.return_value = datetime.combine(today, datetime.min.time())
			mock_choice.return_value = memory1

			result = Memory.select_memory_for_today()

		self.assertEqual(result, memory1)
		# Verify last_selected_on was updated
		memory1.refresh_from_db()
		self.assertEqual(memory1.last_selected_on, today)

	def test_select_memory_for_today_handles_memories_with_null_last_selected_on(self):
		"""Test that select_memory_for_today properly handles memories with null last_selected_on."""
		today = date.today()

		# Create memories, some with null last_selected_on
		Memory.objects.create(
			photo=self.test_photo1, description='Memory with date', last_selected_on=date(2024, 1, 1)
		)

		memory2 = Memory.objects.create(
			photo=self.test_photo2, description='Memory without date', last_selected_on=None
		)

		with (
			patch('core.models.memory.datetime') as mock_datetime,
			patch('core.models.memory.random.choice') as mock_choice,
		):
			mock_datetime.today.return_value = datetime.combine(today, datetime.min.time())
			mock_choice.return_value = memory2

			result = Memory.select_memory_for_today()

		self.assertEqual(result, memory2)
		# Verify last_selected_on was updated from None to today
		memory2.refresh_from_db()
		self.assertEqual(memory2.last_selected_on, today)

	def test_select_memory_for_today_selects_from_oldest_memories(self):
		"""Test that select_memory_for_today selects from memories ordered by last_selected_on (oldest first)."""
		today = date.today()

		# Create memories with different selection dates to test ordering
		memory_recent = Memory.objects.create(
			photo=self.test_photo1, description='Recent memory', last_selected_on=date(2024, 12, 1)
		)

		memory_older = Memory.objects.create(
			photo=self.test_photo2, description='Older memory', last_selected_on=date(2024, 6, 1)
		)

		memory_oldest = Memory.objects.create(
			photo=self.test_photo3, description='Oldest memory', last_selected_on=date(2024, 1, 1)
		)

		# Create memory with null last_selected_on (should be ordered first)
		memory_never_selected = Memory.objects.create(
			photo=SimpleUploadedFile('photo4.jpg', b'photo4 content', content_type='image/jpeg'),
			description='Never selected memory',
			last_selected_on=None,
		)

		# Mock random.choice to capture what memories are passed to it
		with (
			patch('core.models.memory.datetime') as mock_datetime,
			patch('core.models.memory.random.choice') as mock_choice,
		):
			mock_datetime.today.return_value = datetime.combine(today, datetime.min.time())
			mock_choice.return_value = memory_never_selected

			# Capture the arguments passed to random.choice
			Memory.select_memory_for_today()

			# Verify random.choice was called with memories ordered by last_selected_on (oldest first)
			called_memories = list(mock_choice.call_args[0][0])  # Get the queryset passed to random.choice

			# The queryset should contain memories ordered by last_selected_on (ascending, nulls first)
			# Since we're taking the first 10 and we have 4 memories, all should be included
			expected_order = [memory_never_selected, memory_oldest, memory_older, memory_recent]
			self.assertEqual(called_memories, expected_order)
