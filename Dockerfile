# Main build (Django)
FROM python:3.13-slim-trixie

ENV PYTHONUNBUFFERED=1
WORKDIR /app
VOLUME /data

# Create a non-root user to run the app
RUN groupadd --gid ${GID:-1000} django \
  && adduser --disabled-password --gecos "" --home /app --uid ${UID:-1000} --gid ${GID:-1000} django \
  && chown -R django:django /app

# Upgrade and install required system packages
RUN apt update \
  && apt upgrade -y \
  && apt install --no-install-recommends -y build-essential gettext gnupg libxml2-dev libxslt1-dev make python3-dev wget \
  && echo "deb http://apt.postgresql.org/pub/repos/apt trixie-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
  && wget --quiet -O /etc/apt/trusted.gpg.d/postgres.asc https://www.postgresql.org/media/keys/ACCC4CF8.asc \
  && apt update \
  && apt install --no-install-recommends -y postgresql-client-17 libpq-dev \
  && apt purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt clean \
  && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install (if needed) expensive-to-build, big packages and the ones from other indexes (for caching)
RUN --mount=type=cache,target=/var/cache/pip pip install --cache-dir /var/cache/pip -U pip

# Add custom nginx configuration
ADD srv/nginx.conf.sigil /app/

# Install app requirements
COPY --chown=django:django requirements.txt requirements-development.txt /app/
RUN --mount=type=cache,target=/var/cache/pip pip install --cache-dir /var/cache/pip -Ur /app/requirements.txt
ARG ENV_TYPE=production
RUN --mount=type=cache,target=/var/cache/pip if [ "$(echo $ENV_TYPE | tr A-Z a-z)" = "development" ]; then \
    pip install --cache-dir /var/cache/pip -Ur /app/requirements-development.txt; \
  else \
    rm /app/requirements-development.txt; \
  fi

# Copy all needed files and set permissions
COPY --chown=django:django . /app/
USER django
