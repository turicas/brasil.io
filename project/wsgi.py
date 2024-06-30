"""
WSGI config for the project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from django.conf import settings  # noqa
from django.db.backends.signals import connection_created  # noqa
from django.dispatch import receiver  # noqa


@receiver(connection_created)
def setup_postgres(connection, **kwargs):
    if connection.vendor != "postgresql":
        return

    timeout = settings.DATABASE_STATEMENT_TIMEOUT
    with connection.cursor() as cursor:
        cursor.execute(f"SET statement_timeout TO {timeout};")


application = get_wsgi_application()
