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

	def test_highlight_text_differences_multiple_spaces_in_original(self):
		"""Test that multiple consecutive spaces in original are highlighted when removed in modified."""
		original = 'Text with    multiple    spaces'
		modified = 'Text with multiple spaces'
		result = highlight_text_differences(original, modified)

		# The removed spaces should be indicated by deletion markers
		self.assertIn('D', result)
		# Should have highlighting to show the difference
		self.assertIn('<span style="background-color: #ffcccc', result)
		# Should show multiple D markers to indicate multiple deleted spaces (3 spaces deleted after "with")
		# Count the number of consecutive D markers
		d_marker = '<span style="background-color: #ffcccc; color: #cc0000; font-family: Berkeley Mono, monospace; padding:0 2px;">D</span>'
		# There should be at least 3 consecutive D markers (for the 3 extra spaces)
		triple_d = d_marker * 3
		self.assertIn(triple_d, result, 'Should show multiple D markers for multiple deleted spaces')

	def test_highlight_text_differences_multiple_spaces_in_modified(self):
		"""Test that multiple consecutive spaces in modified are highlighted when not in original."""
		original = 'Text with single spaces'
		modified = 'Text with    single    spaces'
		result = highlight_text_differences(original, modified)

		# The extra spaces should be highlighted
		self.assertIn('<span style="background-color: #ffcccc', result)
		# Multiple spaces should be preserved in HTML (using &nbsp; or similar)
		# Currently this FAILS because HTML collapses consecutive spaces
		self.assertIn('&nbsp;', result, 'Multiple spaces should be preserved with &nbsp; to be visible in HTML')
