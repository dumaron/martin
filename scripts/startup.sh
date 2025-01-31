#!/bin/sh
python manage.py migrate
sqlite3 /db/db.sqlite3 'PRAGMA journal_mode=WAL;'
sqlite3 /db/db.sqlite3 'PRAGMA synchronous=1;'
python manage.py runbot & gunicorn --bind :8000 --workers 2 martin.wsgi & supercronic /code/crontab
