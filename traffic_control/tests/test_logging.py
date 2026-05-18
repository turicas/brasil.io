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
    blocked_requests.clear()

    request = request_factory.get("/", HTTP_FOO=42, HTTP_BAR="data")
    log_blocked_request(request, 429)

    assert 1 == len(blocked_requests)
    blocked = blocked_requests.lpop()
    blocked["headers"] = [(key, value) for key, value in blocked["headers"]]  # Change lists into tuples
    assert format_request(request, 429) == blocked
    assert 0 == len(blocked_requests)


def test_extra_propaga_para_request_data(request_factory):
    blocked_requests.clear()
    request = request_factory.get("/api/v1/dataset/foo/bar/data/?page=99999")
    log_blocked_request(request, 400, extra={"block_reason": "deep_pagination_not_allowed"})
    item = blocked_requests.lpop()
    assert 400 == item["response_status_code"]
    assert "deep_pagination_not_allowed" == item["block_reason"]


def test_sem_extra_chave_block_reason_nao_aparece(request_factory):
    blocked_requests.clear()
    request = request_factory.get("/foo")
    log_blocked_request(request, 404)
    item = blocked_requests.lpop()
    assert "block_reason" not in item
