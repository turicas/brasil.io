from model_bakery import baker
from django.urls import reverse_lazy
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
        self.token = baker.make("authtoken.Token", user__is_active=True)
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
