FROM python:3.6.5-alpine

ENV PYTHONUNBUFFERED 1

RUN apk --update add --no-cache \
        git gcc build-base zlib-dev jpeg-dev curl \
        postgresql-dev python3-dev musl-dev libffi-dev

# Requirements have to be pulled and installed here, otherwise caching won't work
COPY ./requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt \
    && rm -rf /requirements.txt

WORKDIR /app

CMD ["cd /"]
