import json
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from covid19.exceptions import SpreadsheetValidationErrors
from covid19.tests.utils import Covid19DatasetTestCase


class ImportSpreadsheetProxyViewTests(TestCase):
    def setUp(self):
        self.url = reverse("covid19:spreadsheet_proxy", args=["RJ"])

    @patch("covid19.views.merge_state_data", autospec=True)
    def test_return_spreadsheet_for_state(self, mock_merge):
        fake_data = {"cases": [], "reports": []}
        mock_merge.return_value = fake_data

        response = self.client.get(self.url)

        assert 200 == response.status_code
        assert fake_data == json.loads(response.content)
        mock_merge.assert_called_once_with("RJ")

    def test_404_if_invalid_state(self):
        self.url = reverse("covid19:spreadsheet_proxy", args=["XX"])
        response = self.client.get(self.url)
        assert 404 == response.status_code

    @patch("covid19.views.merge_state_data", autospec=True)
    def test_400_if_spreadsheet_validation_error(self, mock_merge):
        exception = SpreadsheetValidationErrors()
        exception.new_error("error 1")
        exception.new_error("error 2")
        mock_merge.side_effect = exception

        self.url = reverse("covid19:spreadsheet_proxy", args=["RJ"])
        response = self.client.get(self.url)

        assert 400 == response.status_code
        assert ["error 1", "error 2"] == sorted(response.json()["errors"])


class Covid19DatasetDetailView(Covid19DatasetTestCase):
    def setUp(self):
        self.url = reverse("core:dataset-table-detail", args=["covid19", "caso"])
        call_command("clear_cache")

    def test_display_dataset_table_data_with_expected_template(self):
        response = self.client.get(self.url)
        assert 200 == response.status_code
        self.assertTemplateUsed(response, "dataset-detail.html")

    @override_settings(RATELIMIT_ENABLE=True)
    @override_settings(RATELIMIT_RATE="0/s")
    def test_enforce_rate_limit_if_flagged(self):
        response = self.client.get(self.url)
        assert 429 == response.status_code
        self.assertTemplateUsed(response, "403.html")
        assert "Você atingiu o limite de requisições" in response.context["message"]
