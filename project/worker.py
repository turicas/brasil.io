from rq import Worker


class SentryAwareWorker(Worker):
    def __init__(self, *args, **kwargs):
        from django.conf import settings
        from raven import Client
        from raven.transport import HTTPTransport
        from rq.contrib.sentry import register_sentry

        super().__init__(*args, **kwargs)
        client = Client(settings.SENTRY_DSN, transport=HTTPTransport)
        register_sentry(client, self)
