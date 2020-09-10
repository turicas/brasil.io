"""
WSGI config for brasilio project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
import warnings

from django.core.wsgi import get_wsgi_application

warnings.filterwarnings("ignore", module="environ")  # disable missing .env warning
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "brasilio.settings")

from django.db.backends.signals import connection_created  # noqa
from django.dispatch import receiver  # noqa
from django.conf import settings  # noqa


@receiver(connection_created)
def setup_postgres(connection, **kwargs):
    if connection.vendor != "postgresql":
        return

    timeout = settings.DB_STATEMENT_TIMEOUT
    with connection.cursor() as cursor:
        cursor.execute(f"SET statement_timeout TO {timeout};")


application = get_wsgi_application()
