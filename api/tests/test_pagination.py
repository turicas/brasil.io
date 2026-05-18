from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.urls import reverse_lazy
from model_bakery import baker

from api.exceptions import DeepPaginationNotAllowed
from api.paginators import LargeTablePageNumberPagination, _dataset_code_url
from core.tests.utils import BaseTestCaseWithSampleDataset
from traffic_control.tests.util import TrafficControlClient


def _request(query):
    req = MagicMock()
    req.query_params = query
    return req


def _view(slug=None):
    return MagicMock(kwargs={"slug": slug} if slug else {})


@patch("api.paginators.API_MAX_PAGINATION_RECORDS", 10_000)
class DeepPaginationEnforcementTests(SimpleTestCase):
    def setUp(self):
        self.paginator = LargeTablePageNumberPagination()

    def test_dentro_do_limite_nao_levanta(self):
        self.paginator._enforce_deep_pagination_limit(_request({"page": "1", "page_size": "1000"}), _view())

    def test_exatamente_no_limite_nao_levanta(self):
        self.paginator._enforce_deep_pagination_limit(_request({"page": "10", "page_size": "1000"}), _view())

    def test_acima_do_limite_levanta(self):
        with self.assertRaises(DeepPaginationNotAllowed) as cm:
            self.paginator._enforce_deep_pagination_limit(_request({"page": "11", "page_size": "1000"}), _view())
        exc = cm.exception
        assert 11 == exc.page
        assert 1000 == exc.page_size
        assert 10_000 == exc.limit

    def test_page_size_alto_tambem_eh_pego(self):
        with self.assertRaises(DeepPaginationNotAllowed) as cm:
            self.paginator._enforce_deep_pagination_limit(_request({"page": "2", "page_size": "10000"}), _view())
        assert 20_000 == cm.exception.page * cm.exception.page_size

    def test_page_nao_numerica_nao_dispara(self):
        self.paginator._enforce_deep_pagination_limit(_request({"page": "abc"}), _view())

    def test_page_zero_ou_negativa_nao_dispara(self):
        self.paginator._enforce_deep_pagination_limit(_request({"page": "0", "page_size": "1000"}), _view())
        self.paginator._enforce_deep_pagination_limit(_request({"page": "-1", "page_size": "1000"}), _view())

    def test_limite_zero_desabilita(self):
        with patch("api.paginators.API_MAX_PAGINATION_RECORDS", 0):
            self.paginator._enforce_deep_pagination_limit(_request({"page": "999", "page_size": "1000"}), _view())


@patch("api.paginators.API_MAX_PAGINATION_RECORDS", 10_000)
class DeepPaginationApiTests(BaseTestCaseWithSampleDataset):
    client_class = TrafficControlClient
    DATASET_SLUG = "sample-deep-pagination"
    TABLE_NAME = "sample_table"
    FIELDS_KWARGS = [
        {"name": "sample_field", "options": {"max_length": 10}, "type": "text", "null": False},
    ]

    url = reverse_lazy("v1:dataset-table-data", args=[DATASET_SLUG, TABLE_NAME])

    def setUp(self):
        _dataset_code_url.cache_clear()
        self.dataset.show = True
        self.dataset.save()
        self.token = baker.make("api.Token", user__is_active=True)
        self.auth_header = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}

    def test_acima_do_limite_retorna_400_com_payload_estruturado(self):
        response = self.client.get(f"{self.url}?page=11&page_size=1000", **self.auth_header)
        body = response.json()
        assert 400 == response.status_code
        assert 10_000 == body["limit"]
        assert 11_000 == body["requested"]
        assert "10.000" in body["message"]
        assert "11.000" in body["message"]

    def test_payload_inclui_dataset_url(self):
        response = self.client.get(f"{self.url}?page=11&page_size=1000", **self.auth_header)
        body = response.json()
        assert f"https://brasil.io/dataset/{self.DATASET_SLUG}/" == body["dataset_url"]
        assert f"https://brasil.io/dataset/{self.DATASET_SLUG}/" in body["message"]

    def test_payload_inclui_code_url_quando_dataset_tem(self):
        self.dataset.code_url = "https://github.com/turicas/eleicoes-brasil"
        self.dataset.save(update_fields=["code_url"])
        response = self.client.get(f"{self.url}?page=11&page_size=1000", **self.auth_header)
        body = response.json()
        assert "https://github.com/turicas/eleicoes-brasil" == body["code_url"]
        assert "https://github.com/turicas/eleicoes-brasil" in body["message"]
