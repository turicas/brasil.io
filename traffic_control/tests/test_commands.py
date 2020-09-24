from django.test import RequestFactory, TestCase

from traffic_control.blocked_list import blocked_requests
from traffic_control.commands import PersistBlockedRequestsCommand
from traffic_control.logging import format_request
from traffic_control.models import BlockedRequest


class PersistBlockedRequestsCommandTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_purge_all_blocked_requests(self):
        assert not BlockedRequest.objects.all().exists()
        blocked_requests._requests_data.clear()
        req_1 = format_request(self.factory.get("/"), 429)
        req_2 = format_request(self.factory.get("/login/"), 429)
        blocked_requests.lpush(req_1)
        blocked_requests.lpush(req_2)

        PersistBlockedRequestsCommand.execute()

        assert 2 == BlockedRequest.objects.count()
        assert BlockedRequest.objects.filter(path="/").exists()
        assert BlockedRequest.objects.filter(path="/login/").exists()
