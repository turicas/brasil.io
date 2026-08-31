from django.apps import AppConfig


class BrasilioAuthConfig(AppConfig):
    name = "brasilio_auth"

    def ready(self):
        from brasilio_auth import signals  # noqa: F401
