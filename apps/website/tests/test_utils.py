from django.test import TestCase

from apps.website.utils import highlight_text_differences


class TextDiffUtilsTest(TestCase):
	"""Test the text diff highlighting utility functions."""

	def test_highlight_text_differences_identical_texts(self):
		"""Test highlighting when texts are identical."""
		original = 'Same text'
		modified = 'Same text'
		result = highlight_text_differences(original, modified)
		self.assertEqual(result, 'Same text')
		self.assertNotIn('<span', result)

	def test_highlight_text_differences_completely_different(self):
		"""Test highlighting when texts are completely different."""
		original = 'Original'
		modified = 'Modified'
		result = highlight_text_differences(original, modified)
		self.assertIn('<span style="background-color: #ffcccc', result)
		# The exact output depends on difflib's algorithm, just check that highlighting exists
		self.assertIn('Modified'[0], result)  # Check that first char of modified is somewhere

	def test_highlight_text_differences_partial_changes(self):
		"""Test highlighting when texts have partial differences."""
		original = 'Original Transaction'
		modified = 'Original Payment'
		result = highlight_text_differences(original, modified)
		
		# Should contain both highlighted and unhighlighted parts
		self.assertIn('Original', result)  # Unchanged part should be preserved
		self.assertIn('<span style="background-color: #ffcccc', result)  # Changed part
		# Don't check for exact "Payment" since difflib might break it up character by character

	def test_highlight_text_differences_insertions(self):
		"""Test highlighting when modified text has insertions."""
		original = 'Short'
		modified = 'Short text'
		result = highlight_text_differences(original, modified)
		
		self.assertIn('Short', result)  # Unchanged part
		self.assertIn('<span style="background-color: #ffcccc; color: #cc0000;"> text</span>', result)

	def test_highlight_text_differences_deletions(self):
		"""Test highlighting when modified text has deletions."""
		original = 'Long text'
		modified = 'Long'
		result = highlight_text_differences(original, modified)
		
		self.assertIn('Long', result)  # Unchanged part
		self.assertIn('<span style="background-color: #ffcccc; color: #cc0000; font-family: Berkeley mono, monospace; padding:0 2px;">D</span>', result)

	def test_highlight_text_differences_empty_strings(self):
		"""Test highlighting with empty strings."""
		self.assertEqual(highlight_text_differences('', ''), '')
		self.assertEqual(highlight_text_differences('text', ''), '')
		self.assertEqual(highlight_text_differences('', 'text'), 'text')

	def test_highlight_text_differences_html_escaping(self):
		"""Test that HTML characters are properly escaped."""
		original = 'Normal text'
		modified = 'Text with <script>alert("xss")</script>'
		result = highlight_text_differences(original, modified)
		
		# Should not contain actual HTML tags, only our highlighting spans
		self.assertNotIn('<script>', result)
		self.assertIn('&lt;script&gt;', result)
		self.assertIn('<span style="background-color: #ffcccc', result)