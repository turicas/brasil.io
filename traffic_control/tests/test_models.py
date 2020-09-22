from copy import deepcopy

from django.test import RequestFactory, TestCase

from traffic_control.logging import format_request
from traffic_control.models import BlockedRequest


class BlockedRequestModelTests(TestCase):
    def setUp(self):
        request = RequestFactory().get("/", data={"qs": "v1"}, HTTP_CUSTOM="foo", HTTP_USER_AGENT="agent")
        self.request_data = format_request(request, 429)

    def test_init_blocek_request_from_request_data(self):
        blocked_request = BlockedRequest.from_request_data(deepcopy(self.request_data))

        assert not blocked_request.pk
        assert self.request_data == blocked_request.request_data
        assert "/" == blocked_request.path
        assert 429 == blocked_request.status_code
        assert "agent" == blocked_request.user_agent
        assert "127.0.0.1" == blocked_request.source_ip
        assert {"qs": "v1"} == blocked_request.query_string
        for k, v in self.request_data["headers"]:
            assert v == blocked_request.headers.get(k.lower())

    def test_fail_safe_if_no_request_data(self):
        blocked_request = BlockedRequest.from_request_data({})

        assert {} == blocked_request.request_data
        assert "" == blocked_request.path
        assert 1 == blocked_request.status_code
        assert blocked_request.user_agent is None
        assert blocked_request.source_ip is None
        assert {} == blocked_request.query_string
        assert {} == blocked_request.headers

    def test_source_ip_prioritizes_cloudfare_connection(self):
        self.request_data["headers"].append(("CF-Connecting-Ip", "10.10.10.10"))
        blocked_request = BlockedRequest.from_request_data(deepcopy(self.request_data))
        assert "10.10.10.10" == blocked_request.source_ip

    def test_source_ip_prioritizes_x_forwarded_for_if_no_cloudfare_connection(self):
        self.request_data["headers"].append(("X-Forwarded-For", "10.10.10.10"))
        blocked_request = BlockedRequest.from_request_data(deepcopy(self.request_data))
        assert "10.10.10.10" == blocked_request.source_ip
