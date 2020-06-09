FROM python:3.8
LABEL maintainer="turicas@brasil.io"


# Install system dependencies
RUN apt update
RUN apt install --no-install-recommends -y \
		build-essential \
		gettext \
		libmupdf-dev \
		libpq-dev \
		libxml2-dev \
		libxslt-dev \
		libz-dev \
		postgresql-client \
		python3-dev && \
	apt purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
	apt clean && \
    pip install --no-cache-dir -U pip


COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./start-web.sh /app/start-web.sh
RUN chmod +x /app/start-web.sh

RUN addgroup --system django && \
	adduser --system --ingroup django django
USER django
WORKDIR /app
RUN chown -R django:django /app

CMD ["/app/start-web.sh"]
# TODO: worker?
