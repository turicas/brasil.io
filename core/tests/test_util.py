import pytest
from django.test import RequestFactory

from core.util import ratelimit_key


@pytest.fixture
def request_factory():
    return RequestFactory()


def test_ratelimit_key_from_cloudfare_ip_with_user_agent(request_factory):
    ip, user_agent = "127.1.1.0", "test"

    request = request_factory.get("/", HTTP_CF_CONNECTING_IP=ip, HTTP_USER_AGENT=user_agent)
    key = ratelimit_key("group", request)
    assert f"{ip}:{user_agent}" == key


def test_ratelimit_key_from_x_forwarded_for_ip_with_user_agent(request_factory):
    ip, user_agent = "127.1.1.0,extra_data", "test"

    request = request_factory.get("/", HTTP_X_FORWARDED_FOR=ip, HTTP_USER_AGENT=user_agent)
    key = ratelimit_key("group", request)
    assert f"127.1.1.0:{user_agent}" == key


def test_ratelimit_key_from_remote_addr_with_user_agent(request_factory):
    ip, user_agent = "127.1.1.0", "test"

    request = request_factory.get("/", REMOTE_ADDR=ip, HTTP_USER_AGENT=user_agent)
    key = ratelimit_key("group", request)
    assert f"{ip}:{user_agent}" == key


def test_fail_safe_if_no_explicit_headers(request_factory):
    request = request_factory.get("/")
    key = ratelimit_key("group", request)
    assert "127.0.0.1:" == key
