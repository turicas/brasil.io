# Django build (main image)
FROM python:3.11-bullseye

ENV PYTHONUNBUFFERED 1
ARG DEV_BUILD
WORKDIR /app

RUN echo "deb http://apt.postgresql.org/pub/repos/apt bullseye-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && python -c 'from urllib.request import urlopen; print(urlopen("https://www.postgresql.org/media/keys/ACCC4CF8.asc").read().decode())' > /etc/apt/trusted.gpg.d/postgres.asc \
    && apt update \
    && apt upgrade -y \
    && apt install -y \
           build-essential \
           gettext \
           libpq-dev \
           libz-dev \
           make \
           postgresql-client-14 \
           python3-dev \
           wget \
    && apt purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -U pip

COPY requirements.txt requirements-development.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN if [ "$DEV_BUILD" = "true" ]; then pip install --no-cache-dir -r /app/requirements-development.txt; fi

ADD srv/nginx.conf.sigil /app/
COPY . /app/

CMD "/app/bin/web.sh"
