from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse, reverse_lazy
from model_bakery import baker

from core.tests.utils import BaseTestCaseWithSampleDataset
from traffic_control.tests.util import TrafficControlClient

User = get_user_model()


class DatasetViewSetTests(BaseTestCaseWithSampleDataset):
    client_class = TrafficControlClient
    DATASET_SLUG = "sample"
    TABLE_NAME = "sample_table"
    FIELDS_KWARGS = [
        {"name": "sample_field", "options": {"max_length": 10}, "type": "text", "null": False},
    ]

    url = reverse_lazy("api-v1:dataset-detail", args=[DATASET_SLUG])

    def setUp(self):
        self.dataset.show = True
        self.dataset.save()
        self.token = baker.make("api.Token", user__is_active=True)
        auth = f"Token {self.token.key}"
        self.auth_header = {"HTTP_AUTHORIZATION": auth}

    def test_success_response_if_valid_token(self):
        response = self.client.get(self.url, **self.auth_header)
        assert 200 == response.status_code

    def test_unauthorized_response_if_inactive_user(self):
        self.token.user.is_active = False
        self.token.user.save()
        response = self.client.get(self.url, **self.auth_header)
        assert 401 == response.status_code

    def test_unauthorized_response_if_request_without_auth_token(self):
        url = reverse("brasilio_auth:list_api_tokens")
        expected_msg = f"As credenciais de autenticação não foram fornecidas ou estão inválidas. Acesse https://brasil.io{url} para gerenciar suas chaves de acesso a API."
        response = self.client.get(self.url)
        content = response.json()
        assert 401 == response.status_code
        assert expected_msg == content["message"]

    def test_unauthorized_response_if_request_with_invalid_token(self):
        self.auth_header["HTTP_AUTHORIZATION"] = "Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
        response = self.client.get(self.url, **self.auth_header)
        assert 401 == response.status_code
        self.auth_header["HTTP_AUTHORIZATION"] = "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
        response = self.client.get(self.url, **self.auth_header)
        assert 401 == response.status_code

    def test_404_if_dataset_does_not_exist(self):
        url = reverse_lazy("api-v1:dataset-detail", args=["foooo"])
        response = self.client.get(url, **self.auth_header)
        assert 404 == response.status_code

    def test_404_if_dataset_is_not_visible_for_the_api(self):
        self.dataset.show = False
        self.dataset.save()
        response = self.client.get(self.url, **self.auth_header)
        assert 404 == response.status_code

    @override_settings(ENABLE_API_AUTH=False)
    def test_success_response_with_or_without_valid_token_with_disabled_api_auth(self):
        response = self.client.get(self.url)
        assert 200 == response.status_code
        response = self.client.get(self.url, **self.auth_header)
        assert 200 == response.status_code

    @override_settings(ENABLE_API_AUTH=False)
    def test_unauthorized_response_if_request_with_invalid_token_with_disabled_api_auth(self):
        self.auth_header["HTTP_AUTHORIZATION"] = "Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
        response = self.client.get(self.url, **self.auth_header)
        assert 401 == response.status_code
        self.auth_header["HTTP_AUTHORIZATION"] = "Tokn 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
        response = self.client.get(self.url, **self.auth_header)
        assert 401 == response.status_code


class DatasetTableDataTests(BaseTestCaseWithSampleDataset):
    client_class = TrafficControlClient
    DATASET_SLUG = "sample"
    TABLE_NAME = "sample_table"
    FIELDS_KWARGS = [
        {
            "name": "sample_field",
            "options": {"max_length": 10},
            "type": "text",
            "null": False,
            "filtering": True,
            "choices": {"data": ["foo", "bar"]},
        },
    ]

    url = reverse_lazy("api-v1:dataset-table-data", args=[DATASET_SLUG, TABLE_NAME])

    def setUp(self):
        self.dataset.show = True
        self.dataset.save()
        self.token = baker.make("api.Token", user__is_active=True)
        auth = f"Token {self.token.key}"
        self.auth_header = {"HTTP_AUTHORIZATION": auth}

    def test_400_if_error_with_filter_querystring(self):
        qs = {"sample_field": "invalid_value"}
        response = self.client.get(self.url, data=qs, **self.auth_header)
        assert 400 == response.status_code
        assert "sample_field" in response.json()

    def test_200_if_valid_querystring_data(self):
        qs = {"sample_field": "foo"}
        response = self.client.get(self.url, data=qs, **self.auth_header)
        assert 200 == response.status_code
        assert "results" in response.json()

    def test_404_if_dataset_is_not_visible_for_the_api(self):
        self.dataset.show = False
        self.dataset.save()
        response = self.client.get(self.url, **self.auth_header)
        assert 404 == response.status_code


class TestAPIRedirectsFromPreviousRoutingToVersioned(TestCase):
    client_class = TrafficControlClient

    def test_redirects(self):
        self.client.force_login(baker.make(User))

        path_assertions = [
            (reverse("api-v0:dataset-list"), reverse("api-v1:dataset-list")),
            (reverse("api-v0:dataset-detail", args=["slug"]), reverse("api-v1:dataset-detail", args=["slug"])),
            (
                reverse("api-v0:dataset-table-data", args=["slug", "tablename"]),
                reverse("api-v1:dataset-table-data", args=["slug", "tablename"]),
            ),
            (reverse("api-v0:resource-graph"), reverse("api-v1:resource-graph")),
            (reverse("api-v0:partnership-paths"), reverse("api-v1:partnership-paths")),
            (reverse("api-v0:subsequent-partnerships"), reverse("api-v1:subsequent-partnerships")),
            (reverse("api-v0:company-groups"), reverse("api-v1:company-groups")),
            (reverse("api-v0:node-data"), reverse("api-v1:node-data")),
        ]

        qs = "?foo=1&bar=2"
        for url, redirect_url in path_assertions:
            response = self.client.get(url)
            self.assertRedirects(response, redirect_url, msg_prefix=url, fetch_redirect_response=False, status_code=301)
            response = self.client.get(url + qs)
            self.assertRedirects(
                response, redirect_url + qs, msg_prefix=url, fetch_redirect_response=False, status_code=301
            )

        assert "/api/datasets/" == path_assertions[0][0]
        assert "/api/v1/datasets/" == path_assertions[0][1]

    def test_redirects_from_api_host(self):
        self.client.force_login(baker.make(User))

        urlconf = settings.API_ROOT_URLCONF
        path_assertions = [
            (reverse("api-v0:dataset-list", urlconf=urlconf), reverse("api-v1:dataset-list", urlconf=urlconf)),
            (
                reverse("api-v0:dataset-detail", args=["slug"], urlconf=urlconf),
                reverse("api-v1:dataset-detail", args=["slug"], urlconf=urlconf),
            ),
            (
                reverse("api-v0:dataset-table-data", args=["slug", "tablename"], urlconf=urlconf),
                reverse("api-v1:dataset-table-data", args=["slug", "tablename"], urlconf=urlconf),
            ),
            (reverse("api-v0:resource-graph", urlconf=urlconf), reverse("api-v1:resource-graph", urlconf=urlconf)),
            (
                reverse("api-v0:partnership-paths", urlconf=urlconf),
                reverse("api-v1:partnership-paths", urlconf=urlconf),
            ),
            (
                reverse("api-v0:subsequent-partnerships", urlconf=urlconf),
                reverse("api-v1:subsequent-partnerships", urlconf=urlconf),
            ),
            (reverse("api-v0:company-groups", urlconf=urlconf), reverse("api-v1:company-groups", urlconf=urlconf)),
            (reverse("api-v0:node-data", urlconf=urlconf), reverse("api-v1:node-data", urlconf=urlconf)),
            (reverse("api-v0:api-root", urlconf=urlconf), reverse("api-v1:api-root", urlconf=urlconf)),
        ]

        for url, redirect_url in path_assertions:
            response = self.client.get(url, HTTP_HOST=settings.BRASILIO_API_HOST)
            self.assertRedirects(response, redirect_url, msg_prefix=url, fetch_redirect_response=False, status_code=301)

        assert "/datasets/" == path_assertions[0][0]
        assert "/v1/datasets/" == path_assertions[0][1]


class ApiRootViewTests(TestCase):
    client_class = TrafficControlClient
    url = reverse_lazy("api-v1:api-root")

    def setUp(self):
        self.token = baker.make("api.Token", user__is_active=True)
        auth = f"Token {self.token.key}"
        self.auth_header = {"HTTP_AUTHORIZATION": auth}

    def test_serialize_api_info(self):
        response = self.client.get(self.url, **self.auth_header)
        data = response.json()

        assert 200 == response.status_code
        assert "Brasil.io API" == data["title"]
        assert "api-v1" == data["version"]
        assert reverse("api-v1:dataset-list") == data["datasets_url"]
        assert data["description"]
