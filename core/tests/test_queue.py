from unittest import mock

from django.test import TestCase
from redis import Redis
from rq import Queue

from core.queue import get_redis_queue


class TestGetRedisQueue(TestCase):
    def setUp(self):
        self.m_redis_conn = mock.Mock()
        self.p_redis_from_url = mock.patch.object(Redis, "from_url")
        self.m_redis_from_url = self.p_redis_from_url.start()
        self.m_redis_from_url.return_value = self.m_redis_conn

        self.m_queue = mock.Mock(spec=Queue)
        self.p_queue_cls = mock.patch("core.queue.Queue")
        self.m_queue_cls = self.p_queue_cls.start()
        self.m_queue_cls.return_value = self.m_queue

    def tearDown(self):
        self.p_queue_cls.stop()
        self.m_redis_from_url.stop()

    def test_get_redis_queue_with_custom_arguments(self):
        queue = get_redis_queue(name="name", url="redis://url:6379")

        assert isinstance(queue, Queue)
        self.m_redis_from_url.assert_called_once_with("redis://url:6379")
        self.m_queue_cls.assert_called_once_with(name="name", connection=self.m_redis_conn)
