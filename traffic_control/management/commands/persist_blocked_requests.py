from django.core.management.base import BaseCommand

from traffic_control.commands import PersistBlockedRequestsCommand


class Command(BaseCommand):
    help = "Read blocked requests from redis and persist them on potgres"

    def handle(self, *args, **kwargs):
        PersistBlockedRequestsCommand.execute()
