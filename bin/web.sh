#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

if [ -z ${PORT+x} ]; then
	PORT=5000
fi
if [ -z ${WORKERS+x} ]; then
	WORKERS=4
fi

python manage.py collectstatic --noinput
gunicorn brasilio.wsgi:application \
	--bind="0.0.0.0:$PORT" \
	--chdir=/app \
	--workers=$WORKERS \
	--log-file -
