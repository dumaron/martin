# Martin - Django Project Guidelines

## Agent interaction
- Never extend AGENTS.md if not explicitly required.
- Never add tests unless explicitly asked to do so. Existing tests may be run, and fixed when a change breaks them, but no new test is to be written on your own initiative.
- Never add comments to the code unless explicitly asked to do so. Existing comments must be kept, and updated when a change makes them wrong, but no new comment is to be written on your own initiative.
- `CONVENTIONS.md` is the single source of truth for code style and current practices 

## Commands
- Run server: `pipenv run python manage.py runserver`
- Run all tests: `pipenv run python manage.py test`
- Run unit tests only: `pipenv run python manage.py test --pattern "*_unit_test.py"`
- Run specific test file: `pipenv run python manage.py test apps.website.pages.process_inboxes.process_inboxes_integration_test`
- Run specific test class: `pipenv run python manage.py test apps.website.pages.process_inboxes.process_inboxes_integration_test.ProcessInboxTest`
- Run specific test method: `pipenv run python manage.py test apps.website.pages.process_inboxes.process_inboxes_integration_test.ProcessInboxTest.test_unknown_inbox`
- Lint code: `pipenv run ruff check`
- Format code: `pipenv run ruff format`
- Make migrations: `pipenv run python manage.py makemigrations`
- Apply migrations: `pipenv run python manage.py migrate`

## Code Style
- The project uses `ruff` to ensure code formatting, so it should be executed every time some file is changed

## General
- Remember to add generated files to the current git commit

## Task playbooks
Self-contained instructions for one job each, in the [Agent Skills](https://agentskills.io) format. Read the matching one *before* starting that kind of task:

- `skills/pr-review/SKILL.md` — review the current branch and post inline comments on its GitHub PR.
- `skills/verify/SKILL.md` — run the app against a scratch DB for end-to-end verification.

Claude Code can expose these as `/pr-review` and `/verify` after running `scripts/link-skills.sh` once per clone (`.claude/` is gitignored, so the script creates local symlinks). Other tools should read the files directly.