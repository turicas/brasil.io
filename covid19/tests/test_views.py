import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from covid19.exceptions import SpreadsheetValidationErrors
from traffic_control.tests.util import TrafficControlClient


class ImportSpreadsheetProxyViewTests(TestCase):
    client_class = TrafficControlClient

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
