from unittest import skip
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

import covid19


class TestGoogleDataIntegration(TestCase):
    @skip("This test won't work with Django's DummyCache, which is enabled for development")
    def test_cache_general_spreadsheet(self):
        cache.clear()
        assert not cache.keys("*")

        data = covid19.google_data.get_general_spreadsheet(timeout=10)
        cache_key = cache.keys("*")[0]

        assert data
        assert data == cache.get(cache_key)

    @patch("covid19.google_data.get_general_spreadsheet")
    def test_import_info_by_state_exposes_attr_api(self, mock_import):
        mock_import.return_value = {"SP": {"uf": "SP"}, "RJ": {"uf": "RJ"}, "PR": {"uf": "PR"}}
        rj_data = covid19.google_data.import_info_by_state("RJ")

        assert rj_data.uf == "RJ"
