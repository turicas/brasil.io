import pytest
from unittest.mock import patch

from django.test import TestCase
from django.core.cache import cache

from covid19 import google_data


class TestGoogleDataIntegration(TestCase):
    def test_cache_general_spreadsheet(self):
        cache.clear()
        assert not cache.keys("*")

        data = google_data.get_general_spreadsheet(timeout=10)
        cache_key = cache.keys("*")[0]

        assert data
        assert data == cache.get(cache_key)

    def test_import_info_by_state_exposes_attr_api(self):
        rj_data = google_data.import_info_by_state("RJ")

        assert rj_data.uf == "RJ"

    @patch("covid19.google_data.import_info_by_state")
    def test_retry_to_fetch_google_spreadsheets_if_any_error(self, mock_import):
        mock_import.side_effect = Exception()

        with pytest.raises(Exception):
            google_data.get_state_data_from_google_spreadsheets("RJ")

        mock_import.assert_called_with("RJ")
        assert 3 == mock_import.call_count
