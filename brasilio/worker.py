from raven import Client
from raven.transport import HTTPTransport
from rq import Worker
from rq.contrib.sentry import register_sentry


class SentryAwareWorker(Worker):
    def __init__(self, *args, **kwargs):
        from django.conf import settings

        super().__init__(*args, **kwargs)
        client = Client(settings.SENTRY_DSN, transport=HTTPTransport)
        register_sentry(client, self)
