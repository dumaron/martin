# Martin - Django Project Guidelines

## Agent interaction
- Never extend AGENTS.md if not explicitly required.
- Never add tests unless explicitly asked to do so. Existing tests may be run, and fixed when a change breaks them, but no new test is to be written on your own initiative.
- Never add comments to the code unless explicitly asked to do so. Existing comments must be kept, and updated when a change makes them wrong, but no new comment is to be written on your own initiative.
- `CONVENTIONS.md` is the single source of truth for code style and current practices 

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
- Template partials (included snippets) must be named with a `partial_` prefix (e.g. `partial_fact_row.html`), never a leading underscore (`_fact_row.html`)

## General
- Remember to add generated files to the current git commit

## Task playbooks
Self-contained instructions for one job each, in the [Agent Skills](https://agentskills.io) format. Read the matching one *before* starting that kind of task:

- `skills/pr-review/SKILL.md` — review the current branch and post inline comments on its GitHub PR.
- `skills/verify/SKILL.md` — run the app against a scratch DB for end-to-end verification.

Claude Code can expose these as `/pr-review` and `/verify` after running `scripts/link-skills.sh` once per clone (`.claude/` is gitignored, so the script creates local symlinks). Other tools should read the files directly.