import tempfile


# ruff: noqa
from settings.base import *

# Test-specific settings for GitHub Actions and CI environments
DEBUG = False

# Use temporary directories for media files in tests
MEDIA_ROOT = os.path.join(tempfile.gettempdir(), 'test_media')
os.makedirs(MEDIA_ROOT, exist_ok=True)
MEDIA_URL = '/media/'

# Use in-memory database for faster tests
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}

# Disable logging during tests
LOGGING = {
	'version': 1,
	'disable_existing_loggers': True,
	'handlers': {'null': {'class': 'logging.NullHandler'}},
	'root': {'handlers': ['null']},
}

# Speed up password hashing for tests
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']


# Disable migrations during tests for speed
class DisableMigrations:
	def __contains__(self, item):
		return True

	def __getitem__(self, item):
		return None


MIGRATION_MODULES = DisableMigrations()

# Disable external API calls during tests
YNAB_API_TOKEN = 'test-token'
YNAB_PERSONAL_BUDGET_ID = 'test-budget-id'
YNAB_SHARED_BUDGET_ID = 'test-shared-budget-id'

# Set environment to test
ENVIRONMENT = 'test'
