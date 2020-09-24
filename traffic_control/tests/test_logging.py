from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from traffic_control.blocked_list import blocked_requests
from traffic_control.logging import format_request, log_blocked_request


@pytest.fixture
def request_factory():
    return RequestFactory()


def test_format_simplest_request(request_factory):
    request = request_factory.get("/")
    data = format_request(request, 200)

    assert [] == data["query_string"]
    assert "/" == data["path"]
    assert [("Cookie", "")] == data["headers"]
    assert 200 == data["response_status_code"]
    assert data["user_id"] is None
    assert {"remote-addr": "127.0.0.1", "HTTP_COOKIE": ""} == data["http"]


def test_format_request_query_string(request_factory):
    request = request_factory.get("/", data={"arg1": "foo", "arg2": "bar"})
    data = format_request(request, 200)

    assert [("arg1", "foo"), ("arg2", "bar")] == data["query_string"]


def test_format_custom_headers(request_factory):
    request = request_factory.get("/", HTTP_FOO=42, HTTP_BAR="data")
    data = format_request(request, 200)
    headers = data["headers"]

    assert 3 == len(headers)
    assert ("Foo", 42) in headers
    assert ("Bar", "data") in headers
    assert ("Cookie", "") in headers
    assert 42 == data["http"]["HTTP_FOO"]
    assert "data" == data["http"]["HTTP_BAR"]


def test_format_user_id_for_authenticated_request(request_factory):
    request = request_factory.get("/")
    request.user = Mock(get_user_model(), id=42)
    data = format_request(request, 200)

    assert 42 == data["user_id"]


def test_fail_safe_if_no_remote_addr(request_factory):
    request = request_factory.get("/", HTTP_FOO=42, HTTP_BAR="data")
    request.META.pop("REMOTE_ADDR")

    data = format_request(request, 200)

    assert "" == data["http"]["remote-addr"]


def test_logging_enqueue_message_to_be_processed(request_factory):
    blocked_count = len(blocked_requests)

    request = request_factory.get("/", HTTP_FOO=42, HTTP_BAR="data")
    log_blocked_request(request, 429)

    assert blocked_count + 1 == len(blocked_requests)
    assert format_request(request, 429) == blocked_requests.lpop()
    assert blocked_count == len(blocked_requests)
