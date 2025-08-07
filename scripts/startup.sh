#!/bin/sh
export PYTHONPATH=/code
python manage.py migrate
sqlite3 /storage/db/db.sqlite3 'PRAGMA journal_mode=WAL;'
sqlite3 /storage/db/db.sqlite3 'PRAGMA synchronous=1;'
gunicorn --bind :8000 --workers 2 apps.website.wsgi & supercronic /code/crontab & python apps/telegram_bot/main.py
