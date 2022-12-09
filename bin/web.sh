#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

if [ -z ${PORT+x} ]; then
	PORT=5000
fi
if [ -z ${WEB_WORKERS+x} ]; then
	WEB_WORKERS=4
fi
OPTS="--chdir=/app --bind=0.0.0.0:$PORT --workers=$WEB_WORKERS --log-file -"
if [[ $(echo $DEBUG | tr a-z A-Z) = "TRUE" ]]; then
	OPTS="$OPTS --reload"
fi

python manage.py collectstatic --noinput
gunicorn brasilio.wsgi:application $OPTS
