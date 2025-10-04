#!/bin/sh
mv /Users/duma/dev/martin/db.sqlite3 /Users/duma/dev/martin/db.sqlite3.bk
fly sftp get /storage/db/db.sqlite3 /Users/duma/dev/martin/db.sqlite3
fly sftp get /storage/db/db.sqlite3-wal /Users/duma/dev/martin/db.sqlite3-wal
fly sftp get /storage/db/db.sqlite3-shm /Users/duma/dev/martin/db.sqlite3-shm
sqlite3 /Users/duma/dev/martin/db.sqlite3 'PRAGMA journal_mode=DELETE;'
rm /Users/duma/dev/martin/db.sqlite3-shm