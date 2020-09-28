from django.conf import settings
from django_rq import job

from traffic_control.commands import PersistBlockedRequestsCommand, UpdateBlockedIPsCommand


@job
def persist_blocked_requests_task():
    PersistBlockedRequestsCommand.execute()


@job
def update_blocked_ips_task():
    UpdateBlockedIPsCommand.execute(settings.CLOUDFLARE_ACCOUNT_NAME, settings.CLOUDFLARE_BLOCKED_IPS_RULE)
