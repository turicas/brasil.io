#!/bin/bash

if [ -z "$1" ]; then
	echo "ERROR - Usage: <$0> <dump-filename>"
	exit 1
fi

time pg_restore --verbose --clean --no-acl --no-owner --host=localhost --dbname=$DATABASE_URL $1
