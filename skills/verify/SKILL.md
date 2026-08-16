---
name: verify
description: How to run and drive this Django app against a scratch DB for end-to-end verification without touching the real dev database.
---

# Verifying changes in this repo

The app is a Django site (SQLite). `DATABASE_PATH` env var overrides the DB file (`settings/base.py`), so you can run the real server against a scratch DB:

```bash
DATABASE_PATH=$SCRATCH/verify.sqlite3 pipenv run python manage.py migrate --no-input
DATABASE_PATH=$SCRATCH/verify.sqlite3 pipenv run python manage.py shell -c "
from django.contrib.auth.models import User
User.objects.create_superuser('verify', password='verify')"
DATABASE_PATH=$SCRATCH/verify.sqlite3 pipenv run python manage.py runserver 127.0.0.1:8765 --noreload  # background
```

## Driving it

- All pages require login. Auth is at `/accounts/login/`: GET it with `curl -c jar` to get the csrftoken cookie, then POST `username`, `password`, `csrfmiddlewaretoken` (send `-e <login-url>` as referer).
- Page URLs come from the `Page` class (`apps/website/pages/page.py`): main render at `<base_route>`, actions at `<base_route>/<action-name>`. Check the rendered `<form action=...>` rather than guessing.
- Bank imports need `BankAccount` rows with hardcoded ids (Fineco=2, Credem=3 — see `core/models/bank_transaction.py`); seed them in the scratch DB before importing or the FK constraint fails.

## Gotchas

- Dev `MEDIA_ROOT` is the real `media/` dir in the repo (`settings/dev.py`), so file uploads land in `media/uploads/` even with a scratch DB — delete the files you uploaded afterwards.
- The full `ruff check` fails on pre-existing issues repo-wide; lint only the files you touched.
