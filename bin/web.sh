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
if [ -z ${WEB_TIMEOUT+x} ]; then
  WEB_TIMEOUT=300
fi

HOST_PORT="0.0.0.0:$PORT"
OPTS="--bind=$HOST_PORT --chdir=/app --log-file - --access-logfile - --workers=$GUNICORN_WORKERS --timeout=$WEB_TIMEOUT"
if [[ "$(echo $USE_ASGI | tr a-z A-Z)" = "TRUE" ]]; then
  APP_MODULE="project.asgi:application"
  OPTS="$OPTS --worker-class uvicorn.workers.UvicornWorker"
else
  APP_MODULE="project.wsgi:application"
fi
if [[ $(echo $ENV_TYPE | tr A-Z a-z) = "development" ]]; then
  extra_reload_opts=$(
    find . \( \
        -path './docker' -o \
        -path './.git' -o \
        -path './frontend' -o \
        -path './.local' -o \
        -path './.cache' \
      \) -prune -o \
      -type f \
      -regex '.*\.\(html\|css\|js\|jpg\|gif\|png\|svg\|ttf\|woff\|woff2\|eot\|py\|json\)$' \
      -print \
    | while read -r filename; do
        echo "--reload-extra-file $(dirname "$filename")"
    done | sort -u
  )
  OPTS="$OPTS --reload $extra_reload_opts"
fi

echo "Collecting static files"
python manage.py collectstatic --no-input

echo "Starting Web server"
gunicorn $OPTS $APP_MODULE
