import json
from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError
from django.test import Client, RequestFactory, TestCase, override_settings
from django_ratelimit.exceptions import Ratelimited
from model_bakery import baker
from psycopg2.errors import QueryCanceled

from traffic_control.middlewares import BLOCKED_REQUEST_ATTR, CatchStatementTimeoutMiddleware, block_suspicious_requests


class BlockSuspiciousRequestsMiddlewareTests(TestCase):
    def assert429(self, response):
        assert 429 == response.status_code
        self.assertTemplateUsed(response, "4xx.html")
        assert self.invalid_string not in response.content.decode()
        assert "Você atingiu o limite de requisições" in response.context["message"]
        assert 429 == response.context["title_4xx"]

    def test_bad_request_if_no_user_agent(self):
        self.invalid_string = "Invalid: '%s'"
        settings.TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = self.invalid_string
        response = self.client.get("/")
        self.assert429(response)

    @override_settings(BLOCKED_WEB_AGENTS="invalid_agent")
    def test_bad_request_if_blocked_user_agent(self):
        self.invalid_string = "Invalid: '%s'"
        settings.TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = self.invalid_string
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

    def test_flag_request_with_blocked_request_attr(self):
        get_response = Mock()
        request = RequestFactory().get("/")

        middleware = block_suspicious_requests(get_response)
        with pytest.raises(Ratelimited):
            middleware(request)

        assert not get_response.called
        assert getattr(request, BLOCKED_REQUEST_ATTR, False)


@pytest.fixture
def request_factory():
    return RequestFactory()


TIMEOUT_MESSAGE = "canceling statement due to statement timeout\n"


def _process_exception(request, exc):
    return CatchStatementTimeoutMiddleware(get_response=None).process_exception(request, exc)


def test_query_canceled_em_view_de_api_retorna_503(request_factory):
    request = request_factory.get("/api/v1/dataset/foo/bar/data/")
    with patch("traffic_control.middlewares.report_error"):
        response = _process_exception(request, QueryCanceled(TIMEOUT_MESSAGE))
    assert 503 == response.status_code
    assert "sobrecarregado" in json.loads(response.content)["message"].lower()


def test_operational_error_com_statement_timeout_retorna_503(request_factory):
    request = request_factory.get("/api/v1/dataset/foo/bar/data/")
    with patch("traffic_control.middlewares.report_error"):
        response = _process_exception(request, OperationalError(TIMEOUT_MESSAGE))
    assert 503 == response.status_code


def test_operational_error_sem_mensagem_de_timeout_nao_trata(request_factory):
    request = request_factory.get("/api/v1/dataset/foo/bar/data/")
    with patch("traffic_control.middlewares.report_error") as captura:
        response = _process_exception(request, OperationalError("connection closed"))
    assert response is None
    assert not captura.called


def test_excecao_de_outro_tipo_nao_trata(request_factory):
    request = request_factory.get("/api/v1/dataset/foo/bar/data/")
    with patch("traffic_control.middlewares.report_error") as captura:
        response = _process_exception(request, ValueError(TIMEOUT_MESSAGE))
    assert response is None
    assert not captura.called


def test_query_canceled_fora_da_api_reporta_e_deixa_virar_500(request_factory):
    request = request_factory.get("/datasets/")
    with patch("traffic_control.middlewares.report_error") as captura:
        response = _process_exception(request, QueryCanceled(TIMEOUT_MESSAGE))
    assert response is None
    assert captura.called


def test_query_canceled_reporta_com_exception_e_tag_kind(request_factory):
    request = request_factory.get("/api/v1/dataset/foo/bar/data/")
    exc = QueryCanceled(TIMEOUT_MESSAGE)
    with patch("traffic_control.middlewares.report_error") as captura:
        _process_exception(request, exc)
    captura.assert_called_once()
    kwargs = captura.call_args.kwargs
    assert exc is kwargs["exception"]
    assert {"kind": "statement_timeout"} == kwargs["tags"]
    assert "error" == kwargs["level"]


@pytest.mark.django_db
def test_statement_timeout_em_view_real_da_api_retorna_503(settings):
    """Passa pelo pipeline completo de middlewares: garante que a exceção da view chega ao middleware."""
    settings.DEBUG = False
    token = baker.make("api.Token", user=baker.make(get_user_model(), is_active=True))
    client = Client(raise_request_exception=False)
    with patch("api.views.ApiRootView.get", side_effect=OperationalError(TIMEOUT_MESSAGE)), patch(
        "traffic_control.middlewares.report_error"
    ) as captura, patch("django.utils.log.AdminEmailHandler.emit"):
        response = client.get(
            "/v1/",
            HTTP_USER_AGENT="cliente-legitimo",
            HTTP_HOST=settings.BRASILIO_API_HOST,
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
    assert 503 == response.status_code
    assert "sobrecarregado" in json.loads(response.content)["message"].lower()
    captura.assert_called_once()
