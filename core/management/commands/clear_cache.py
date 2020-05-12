from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clear cache"

    def handle(self, *args, **kwargs):
        cache.clear()
