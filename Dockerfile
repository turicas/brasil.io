FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED 1
ARG DEV_BUILD
WORKDIR /app
VOLUME /data

RUN apt update \
  && apt install -y build-essential gettext gnupg make python3-dev wget \
  && echo "deb http://apt.postgresql.org/pub/repos/apt bullseye-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
  && wget --quiet -O /etc/apt/trusted.gpg.d/postgres.asc https://www.postgresql.org/media/keys/ACCC4CF8.asc \
  && apt update \
  && apt install -y postgresql-client-17 libpq-dev \
  && apt upgrade -y \
  && apt purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt clean \
  && rm -rf /var/lib/apt/lists/*

RUN addgroup --gid ${GID:-1000} django \
  && adduser --disabled-password --gecos "" --home /app --uid ${UID:-1000} --gid ${GID:-1000} django \
  && chown -R django:django /app
ADD srv/nginx.conf.sigil /app/

COPY requirements.txt /app/
COPY requirements-development.txt /app/
RUN pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -Ur /app/requirements.txt \
  && if [ "$(echo $DEV_BUILD | tr A-Z a-z)" = "true" ]; then pip install --no-cache-dir -Ur /app/requirements-development.txt; fi

COPY . /app/
RUN chown -R django:django /app
USER django
