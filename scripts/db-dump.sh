#!/bin/bash

mkdir -p /data/backups
BACKUP_FILENAME="/data/backups/brasilio-$(date +'%Y-%m-%dT%H:%M:%S').dump"

TABLE_NAMES_SQL="SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name NOT LIKE 'data_%' AND table_name NOT LIKE 'pghero_%'"
PG_IP=$(dokku postgres:info brasilio_pg11 | grep -i 'ip:' | awk '{print $3}')
DATABASE_URL=$(dokku config:get brasilio-web DATABASE_URL | sed 's/@.*:/@$PG_IP:/')
TABLE_OPTS=$(echo "COPY ($TABLE_NAMES_SQL) TO STDIN DELIMITER ',' CSV" | psql $DATABASE_URL | sed 's/^/-t /; s/$/ /' | paste -sd ' ' -)

time pg_dump --format=c $TABLE_OPTS --file="$BACKUP_FILENAME" $DATABASE_URL
