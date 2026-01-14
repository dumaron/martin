# Martin - Django Project Guidelines

## Project Info
- Django version: 6.0
- Python version: 3.12

## Django 6.0 Migration Notes
After migrating from Django 5.x to 6.0:

### Completed Updates
- ✅ Pinned all package versions in Pipfile to current installed versions
- ✅ Added Django 6.0 to Pipfile with explicit version pinning
- ✅ Migrated from deprecated `STATICFILES_STORAGE` to `STORAGES["staticfiles"]` configuration
- ✅ Updated documentation URLs from Django 5.0 to 6.0
- ✅ Fixed collectstatic error by switching from `CompressedManifestStaticFilesStorage` to `CompressedStaticFilesStorage` (handles missing source map files)

### Breaking Changes to Be Aware Of
- `DEFAULT_AUTO_FIELD` now defaults to `BigAutoField` (was `AutoField` in Django 5.x)
- Python 3.12+ is required (3.10 and 3.11 no longer supported)
- Email API changes: `EmailMessage.message()` now returns `email.message.EmailMessage` instead of `SafeMIMEText`/`SafeMIMEMultipart`

## Commands
- Run server: `pipenv run python manage.py runserver`
- Run all tests: `pipenv run python manage.py test`
- Run specific test: `pipenv run python manage.py test finances.tests.test_models_import`
- Run specific test class: `pipenv run python manage.py test finances.tests.test_models_import.TestClassName`
- Run specific test method: `pipenv run python manage.py test finances.tests.test_models_import.TestClassName.test_method`
- Lint code: `pipenv run ruff check`
- Format code: `pipenv run ruff format`
- Make migrations: `pipenv run python manage.py makemigrations`
- Apply migrations: `pipenv run python manage.py migrate`

## Code Style
- Line length: 110 characters
- Indentation: Tabs (width of 1)
- Quotes: Single quotes
- Python version: 3.12
- Imports: Sort with isort (standard → third-party → local)
- Classes: PascalCase
- Functions/variables: snake_case
- Django models: One model per file in dedicated models directory
- Error handling: Use try/except with specific exceptions
- Comments: Docstrings for complex functions
- Structure: Follow Django app-based architecture
- Always add newly created files to git staging area.