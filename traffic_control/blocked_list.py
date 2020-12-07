import json
from collections import deque

from cached_property import cached_property
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

    @cached_property
    def redis_conn(self):
        if settings.RQ_BLOCKED_REQUESTS_LIST:
            return get_redis_connection("default")

    def lpush(self, request_data):
        if self.redis_conn:
            self.redis_conn.lpush(settings.RQ_BLOCKED_REQUESTS_LIST, json.dumps(request_data))
        else:
            self._requests_data.appendleft(request_data)

    def lpop(self):
        if self.redis_conn:
            return json.loads(self.redis_conn.lpop(settings.RQ_BLOCKED_REQUESTS_LIST))
        else:
            return self._requests_data.popleft()

    def __len__(self):
        if self.redis_conn:
            return self.redis_conn.llen(settings.RQ_BLOCKED_REQUESTS_LIST)
        else:
            return len(self._requests_data)

    def clear(self):
        if self.redis_conn:
            while len(self) > 0:
                self.lpop()
        else:
            self._requests_data.clear()


blocked_requests = BlockedRequestList()
