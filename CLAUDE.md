# Martin - Django Project Guidelines

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