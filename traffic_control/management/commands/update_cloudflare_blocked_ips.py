from django.conf import settings
from django.core.management.base import BaseCommand

from traffic_control.commands import UpdateBlockedIPsCommand


class Command(BaseCommand):
    help = "Update Cloudflare blocked ips"

    def add_arguments(self, parser):
        parser.add_argument("--hours-ago", required=False, type=int)
        parser.add_argument("--hourly-max", required=False, type=int)
        parser.add_argument("--daily-max", required=False, type=int)

    def handle(self, *args, **kwargs):
        hourly_max = kwargs["hourly_max"] or 30
        daily_max = kwargs["daily_max"] or 1200
        hours_ago = kwargs["hours_ago"]

        UpdateBlockedIPsCommand.execute(
            settings.CLOUDFLARE_ACCOUNT_NAME,
            settings.CLOUDFLARE_BLOCKED_IPS_RULE,
            hourly_max=hourly_max,
            daily_max=daily_max,
            hours_ago=hours_ago,
        )
