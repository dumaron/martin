#!/bin/sh
set -e

fly ssh console -C 'sqlite3 /storage/db/db.sqlite3 ".backup /tmp/db_backup.sqlite3"'
mv /Users/duma/dev/martin/db.sqlite3 /Users/duma/dev/martin/db.sqlite3.bk
fly sftp get /tmp/db_backup.sqlite3 /Users/duma/dev/martin/db.sqlite3
fly ssh console -C 'rm /tmp/db_backup.sqlite3'
