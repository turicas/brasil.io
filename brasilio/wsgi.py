"""
WSGI config for brasilio project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "brasilio.settings")

from django.db.backends.signals import connection_created
from django.dispatch import receiver
from django.conf import settings


@receiver(connection_created)
def setup_postgres(connection, **kwargs):
    if connection.vendor != "postgresql":
        return

    timeout = settings.DB_STATEMENT_TIMEOUT
    with connection.cursor() as cursor:
        cursor.execute(f"SET statement_timeout TO {timeout};")


application = get_wsgi_application()
