# Django build (main image)
FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
WORKDIR /app

RUN apt update \
  && apt install -y build-essential gettext libmupdf-dev libpq-dev libxml2-dev libxslt-dev libz-dev postgresql-client python3-dev \
  && apt purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r /app/requirements.txt

ADD srv/nginx.conf.sigil /app/
COPY . /app/

CMD "/app/bin/web.sh"
