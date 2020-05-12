import rq
from rq.contrib.sentry import register_sentry

from raven import Client
from raven.transport import HTTPTransport


class SentryAwareWorker(rq.Worker):
    def __init__(self, *args, **kwargs):
        from django.conf import settings

        super().__init__(*args, **kwargs)
        client = Client(settings.SENTRY_DSN, transport=HTTPTransport)
        register_sentry(client, self)
