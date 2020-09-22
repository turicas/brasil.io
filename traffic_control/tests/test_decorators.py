import pytest
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from ratelimit.exceptions import Ratelimited

from traffic_control.decorators import enable_ratelimit


def fake_view(request, foo, bar):
    return HttpResponse(f"content: {foo} and {bar}")


class EnableRateLimitDecoratorTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        self.rate_limit_view = enable_ratelimit(fake_view)

    @override_settings(RATELIMIT_ENABLE=False)
    @override_settings(RATELIMIT_RATE="0/s")
    def test_valid_request_if_ratelimit_is_not_enabled(self):
        response = self.rate_limit_view(self.request, "foo_arg", "bar_arg")
        assert 200 == response.status_code
        assert "content: foo_arg and bar_arg"

    @override_settings(RATELIMIT_ENABLE=True)
    @override_settings(RATELIMIT_RATE="10/s")
    def test_valid_request_if_ratelimit_enabled_but_under_threshold(self):
        response = self.rate_limit_view(self.request, "foo_arg", "bar_arg")
        assert 200 == response.status_code
        assert "content: foo_arg and bar_arg"

    @override_settings(RATELIMIT_ENABLE=True)
    @override_settings(RATELIMIT_RATE="0/s")
    def test_raise_rate_limited_exception_if_exceeding_threshold(self):
        with pytest.raises(Ratelimited):
            self.rate_limit_view(self.request, "foo_arg", "bar_arg")
