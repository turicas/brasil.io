import json
from collections import deque

from django.conf import settings
from django_redis import get_redis_connection


class BlockedRequestList:
    """
    Singleton indirection between our code and Redis to isolate how we're enqueing the request
    data to be further read by the system. Doing this also allow us to unit test it without
    relying on complicated mocking strategies. Import as:

    from traffic_control.blocked_list import blocked_requests
    """

    def __init__(self):
        self._requests_data = deque()

    def lpush(self, request_data):
        if settings.RQ_BLOCKED_REQUESTS_LIST:
            conn = get_redis_connection("default")
            conn.lpush(settings.RQ_BLOCKED_REQUESTS_LIST, json.dumps(request_data))
        else:
            self._requests_data.appendleft(request_data)
            print(f"BLOCKED REQUEST - Response {request_data}")

    def lpop(self):
        if settings.RQ_BLOCKED_REQUESTS_LIST:
            conn = get_redis_connection("default")
            return json.loads(conn.lpop(settings.RQ_BLOCKED_REQUESTS_LIST))
        else:
            return self._requests_data.popleft()

    def __len__(self):
        return len(self._requests_data)


blocked_requests = BlockedRequestList()
