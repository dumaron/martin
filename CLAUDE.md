# Martin - Django Project Guidelines

## Project Info
- Refer to pipenv for versions

## Claude interaction
- Never not extend CLAUDE.md if not explicitly required.

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
- The project uses `ruff` to ensure code formatting, so it should be executed every time some file is changed
- Try to use some functional programming patterns when they make sense

## General
- Remember to add generated files to the current git commit