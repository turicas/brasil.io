#!/bin/bash

set -e

docker stop brasilio_postgres
docker rm brasilio_postgres
source .activate

if [ -f "latest.dump" ]; then
	source .env
	export PGPASSWORD="$POSTGRES_PASSWORD"
	sleep 5
	pg_restore --verbose --clean --no-acl --no-owner \
	           --host=localhost --port=$POSTGRES_PORT \
	           -user=$POSTGRES_USER --dbname=$POSTGRES_DB \
		latest.dump
fi
