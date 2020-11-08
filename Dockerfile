# Django build
FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  && apt-get install -y build-essential gettext libmupdf-dev libpq-dev libxml2-dev libxslt-dev libz-dev postgresql-client python3-dev \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN addgroup --system django \
  && adduser --system --ingroup django django

COPY requirements.txt /app/
RUN pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r /app/requirements.txt

COPY --chown=django:django . /app/
ADD srv/nginx.conf.sigil /app/
RUN chown django:django /app
USER django
WORKDIR /app

CMD "/app/bin/web.sh"
