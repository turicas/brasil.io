from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from core.tests.utils import TestCaseWithSampleDataset


class SampleDatasetDetailView(TestCaseWithSampleDataset):
    DATASET_SLUG = "sample"
    TABLE_NAME = "sample_table"
    FIELDS_KWARGS = [
        {"name": "sample_field", "options": {"max_length": 10}, "type": "text", "null": False},
    ]

    def setUp(self):
        self.url = reverse("core:dataset-table-detail", args=["sample", "sample_table"])
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
