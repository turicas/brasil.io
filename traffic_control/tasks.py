from django_rq import job

from traffic_control.commands import PersistBlockedRequestsCommand


@job
def persist_blocked_requests_task():
    PersistBlockedRequestsCommand.execute()
