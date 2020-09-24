from unittest.mock import patch

from traffic_control import tasks
from traffic_control.commands import PersistBlockedRequestsCommand


@patch("traffic_control.tasks.PersistBlockedRequestsCommand.execute", spec=PersistBlockedRequestsCommand.execute)
def test_persist_blocked_requests_async_task(mocked_command):
    assert getattr(tasks.persist_blocked_requests_task, "delay")  # ensure it's a job
    tasks.persist_blocked_requests_task()
    mocked_command.assert_called_once_with()
