from django.test import TestCase, override_settings


class BlockSuspiciousRequestsMiddlewareTests(TestCase):
    def assert429(self, response):
        assert 429 == response.status_code
        self.assertTemplateUsed(response, "4xx.html")
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
