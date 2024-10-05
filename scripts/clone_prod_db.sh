#!/bin/sh
mv /Users/duma/dev/martin/db.sqlite3 /Users/duma/dev/martin/db.sqlite3.bk
fly sftp get /db/db.sqlite3 /Users/duma/dev/martin/db.sqlite3 
sqlite3 /Users/duma/dev/martin/db.sqlite3 'PRAGMA journal_mode=DELETE;'