import shutil
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings


@override_settings(MEDIA_ROOT=Path(settings.MEDIA_ROOT) / 'test_files')
class FileCleanupTestCase(TestCase):
	"""
	Base test case class that ensures proper cleanup of uploaded files.

	This class automatically:
	- Creates a test-specific media directory for each test
	- Cleans up all uploaded files after each test completes
	- Prevents test pollution between different test runs
	"""

	@classmethod
	def setUpClass(cls):
		"""Set up test class - create test media directory."""
		super().setUpClass()
		cls.test_media_root = Path(settings.MEDIA_ROOT)
		cls.test_media_root.mkdir(parents=True, exist_ok=True)

	def tearDown(self):
		"""Clean up uploaded files after each test."""
		super().tearDown()
		# Remove all files created during the test
		if self.test_media_root.exists():
			shutil.rmtree(self.test_media_root)
			self.test_media_root.mkdir(parents=True, exist_ok=True)

	@classmethod
	def tearDownClass(cls):
		"""Clean up test media directory after all tests in the class complete."""
		super().tearDownClass()
		if cls.test_media_root.exists():
			shutil.rmtree(cls.test_media_root)
