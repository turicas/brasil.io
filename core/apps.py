from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        from .models import Table
        for table in Table.objects.all():
            _ = table.get_model()
