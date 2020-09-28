from unittest.mock import Mock, patch

from django.conf import settings

from traffic_control import tasks
from traffic_control.commands import PersistBlockedRequestsCommand, UpdateBlockedIPsCommand


@patch("traffic_control.tasks.PersistBlockedRequestsCommand.execute", spec=PersistBlockedRequestsCommand.execute)
def test_persist_blocked_requests_async_task(mocked_command):
    assert getattr(tasks.persist_blocked_requests_task, "delay")  # ensure it's a job
    tasks.persist_blocked_requests_task()
    mocked_command.assert_called_once_with()


@patch("traffic_control.tasks.UpdateBlockedIPsCommand.execute", Mock(), spec=UpdateBlockedIPsCommand.execute)
def test_update_blocked_ips_async_task():
    from traffic_control.tasks import UpdateBlockedIPsCommand

    assert getattr(tasks.update_blocked_ips_task, "delay")  # ensure it's a job
    tasks.update_blocked_ips_task()
    UpdateBlockedIPsCommand.execute.assert_called_once_with(
        settings.CLOUDFLARE_ACCOUNT_NAME, settings.CLOUDFLARE_BLOCKED_IPS_RULE
    )
