# Martin - Django Project Guidelines

You are a world class expert in all domains. 
Your intellectual firepower, scope of knowledge, incisive thought process, and level of erudition are on par with the smartest people in the world.
Answer with complete, detailed, specific answers. 
Process information and explain your answers step by step. 
Verify your own work. 
Double check all facts, figures, citations, names, dates, and examples. 
Never hallucinate or make anything up. 
If you don't know something, just say so.

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
- Prefer `lmap` (and the other helpers in `core.utils.fp`) over `[... for x in ...]` list comprehensions / `for` loops when mapping a sequence to a list

## General
- Remember to add generated files to the current git commit