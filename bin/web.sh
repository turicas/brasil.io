#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

if [ -z ${PORT+x} ]; then
	PORT=5000
fi
if [ -z ${USE_ASGI+x} ]; then
	USE_ASGI=false
fi
if [ -z ${GUNICORN_WORKERS+x} ]; then
	GUNICORN_WORKERS=20
fi

HOST_PORT="0.0.0.0:$PORT"
OPTS="--bind=$HOST_PORT --chdir=/app --log-file - --access-logfile - --workers=$GUNICORN_WORKERS"
if [[ "$(echo $USE_ASGI | tr a-z A-Z)" = "TRUE" ]]; then
	APP_MODULE="project.asgi:application"
	OPTS="$OPTS --worker-class uvicorn.workers.UvicornWorker"
else
	APP_MODULE="project.wsgi:application"
fi
if [[ $(echo $DEV_BUILD | tr a-z A-Z) = "TRUE" ]]; then
	extra_reload_opts=$(
		find -regextype posix-extended -regex '.*/(templates|static)/?$' \
		| while read path; do
			echo --reload-extra-file $path
		done
	)
	OPTS="$OPTS --reload $extra_reload_opts"
fi

python manage.py collectstatic --no-input
gunicorn $OPTS $APP_MODULE
