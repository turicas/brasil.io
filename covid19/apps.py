from django.apps import AppConfig


class Covid19Config(AppConfig):
    name = "covid19"

    def ready(self):
        try:
            import covid19.signals  # noqa F401
        except ImportError:
            pass
