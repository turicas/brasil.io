from django.conf import settings
from django.test import TestCase, override_settings


class BlockSuspiciousRequestsMiddlewareTests(TestCase):
    def assert429(self, response):
        assert 429 == response.status_code
        self.assertTemplateUsed(response, "4xx.html")
        assert settings.TEMPLATE_STRING_IF_INVALID not in response.content.decode()
        assert "Você atingiu o limite de requisições" in response.context["message"]
        assert 429 == response.context["title_4xx"]

    def test_bad_request_if_no_user_agent(self):
        response = self.client.get("/")
        self.assert429(response)

    @override_settings(BLOCKED_WEB_AGENTS="invalid_agent")
    def test_bad_request_if_blocked_user_agent(self):
        response = self.client.get("/", HTTP_USER_AGENT="invalid_agent")
        self.assert429(response)

    @override_settings(BLOCKED_WEB_AGENTS="invalid_agent")
    def test_valid_request_if_allowed_user_agent(self):
        response = self.client.get("/", HTTP_USER_AGENT="other_agent")
        assert 429 != response.status_code

    def test_middleware_pipeline_does_not_break_if_invalid_resolve(self):
        response = self.client.get("alkjsdasd3121312", HTTP_USER_AGENT="other_agent")
        assert 404 == response.status_code

    def test_middleware_respects_append_slash_setings(self):
        url = "/admin"
        with override_settings(APPEND_SLASH=True):
            response = self.client.get(url, HTTP_USER_AGENT="other_agent")
            assert 404 != response.status_code
        with override_settings(APPEND_SLASH=False):
            response = self.client.get(url, HTTP_USER_AGENT="other_agent")
            assert 404 == response.status_code
