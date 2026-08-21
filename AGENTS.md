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

## Agent interaction
- Never not extend AGENTS.md if not explicitly required.
- Never add tests unless explicitly asked to do so. Existing tests may be run, and fixed when a change breaks them, but no new test is to be written on your own initiative.
- Never add comments to the code unless explicitly asked to do so. Existing comments must be kept, and updated when a change makes them wrong, but no new comment is to be written on your own initiative.

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
- Template partials (included snippets) must be named with a `partial_` prefix (e.g. `partial_fact_row.html`), never a leading underscore (`_fact_row.html`)

## General
- Remember to add generated files to the current git commit

## Architecture
See `CONVENTIONS.md` for how this project departs from standard Django: business logic in `core/`, presentation layers in `apps/`, and the `Page` class instead of views + `urlpatterns`.

## Task playbooks
Self-contained instructions for one job each, in the [Agent Skills](https://agentskills.io) format. Read the matching one *before* starting that kind of task:

- `skills/pr-review/SKILL.md` — review the current branch and post inline comments on its GitHub PR.
- `skills/verify/SKILL.md` — run the app against a scratch DB for end-to-end verification.

Claude Code can expose these as `/pr-review` and `/verify` after running `scripts/link-skills.sh` once per clone (`.claude/` is gitignored, so the script creates local symlinks). Other tools should read the files directly.