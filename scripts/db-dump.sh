#!/bin/bash

HOST_BACKUP_PATH="/storage/backup"
CONTAINER_BACKUP_PATH="/data"
BACKUP_FILENAME="pg17_brasil-io-prd-$(date +'%Y-%m-%dT%H:%M:%S').dump"

TABLE_NAMES_SQL="SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name NOT LIKE 'data_%' AND table_name NOT LIKE 'pghero_%'"
PG_IP=$(dokku postgres:info pg17_brasil-io-prd | grep -i 'ip:' | awk '{print $3}')
DATABASE_URL=$(dokku config:get brasil-io-prd DATABASE_URL | sed "s/@.*:/@$PG_IP:/")
TABLE_OPTS=$(echo "COPY ($TABLE_NAMES_SQL) TO STDIN DELIMITER ',' CSV" | psql $DATABASE_URL | sed 's/^/-t /; s/$/ /' | paste -sd ' ' -)

time docker run --rm -it -v "${HOST_BACKUP_PATH}:${CONTAINER_BACKUP_PATH}" postgres:17.6-trixie \
  pg_dump --format=c $TABLE_OPTS --file="${CONTAINER_BACKUP_PATH}/${BACKUP_FILENAME}" $DATABASE_URL
