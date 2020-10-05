from django.urls import reverse_lazy
from model_bakery import baker

from core.tests.utils import BaseTestCaseWithSampleDataset
from traffic_control.tests.util import TrafficControlClient


class DatasetViewSetTests(BaseTestCaseWithSampleDataset):
    client_class = TrafficControlClient
    DATASET_SLUG = "sample"
    TABLE_NAME = "sample_table"
    FIELDS_KWARGS = [
        {"name": "sample_field", "options": {"max_length": 10}, "type": "text", "null": False},
    ]

    url = reverse_lazy("api:dataset-detail", args=[DATASET_SLUG])

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
        response = self.client.get(self.url)
        assert 401 == response.status_code

    def test_unauthorized_response_if_request_with_invalid_token(self):
        self.auth_header["HTTP_AUTHORIZATION"] = "Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
        response = self.client.get(self.url, **self.auth_header)
        assert 401 == response.status_code

    def test_404_if_dataset_does_not_exist(self):
        url = reverse_lazy("api:dataset-detail", args=["foooo"])
        response = self.client.get(url, **self.auth_header)
        assert 404 == response.status_code

    def test_404_if_dataset_is_not_visible_for_the_api(self):
        self.dataset.show = False
        self.dataset.save()
        response = self.client.get(self.url, **self.auth_header)
        assert 404 == response.status_code


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

    url = reverse_lazy("api:dataset-table-data", args=[DATASET_SLUG, TABLE_NAME])

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
