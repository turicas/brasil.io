from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from model_bakery import baker

from core.models import TableFile
from core.tests.utils import BaseTestCaseWithSampleDataset
from traffic_control.tests.util import TrafficControlClient


class SampleDatasetDetailView(BaseTestCaseWithSampleDataset):
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

    def setUp(self):
        self.url = reverse("core:dataset-table-detail", args=["sample", "sample_table"])
        call_command("clear_cache")

    def test_display_dataset_table_data_with_expected_template(self):
        response = self.client.get(self.url)
        assert 200 == response.status_code
        self.assertTemplateUsed(response, "core/dataset-detail.html")
        assert settings.TEMPLATE_STRING_IF_INVALID not in response.content.decode()
        assert "" == response.context["search_term"]

    def test_400_if_invalid_filter_choice(self):
        url = self.url + "?sample_field=xpto&search=algo"
        response = self.client.get(url)
        assert 400 == response.status_code
        self.assertTemplateUsed(response, "core/dataset-detail.html")
        assert settings.TEMPLATE_STRING_IF_INVALID not in response.content.decode()
        assert "sample_field" in response.context["filter_form"].errors
        assert "algo" == response.context["search_term"]

    @override_settings(RATELIMIT_ENABLE=True)
    @override_settings(RATELIMIT_RATE="0/s")
    @patch("traffic_control.decorators.ratelimit")
    def test_enforce_rate_limit_if_flagged(self, mocked_ratelimit):
        response = self.client.get(self.url)
        assert 429 == response.status_code
        self.assertTemplateUsed(response, "4xx.html")
        assert settings.TEMPLATE_STRING_IF_INVALID not in response.content.decode()
        assert "Você atingiu o limite de requisições" in response.context["message"]
        assert 429 == response.context["title_4xx"]
        assert mocked_ratelimit.called is False  # this ensures the middleware is the one raising the 429 error


class TestDatasetFilesDetailView(BaseTestCaseWithSampleDataset):
    client_class = TrafficControlClient
    DATASET_SLUG = "sample"
    TABLE_NAME = "sample_table"
    FIELDS_KWARGS = [
        {"name": "sample_field", "options": {"max_length": 10}, "type": "text", "null": False},
    ]

    def setUp(self):
        self.url = reverse("core:dataset-files-detail", args=[self.dataset.slug])
        baker.make(TableFile, table=self.table)

    def test_render_template_with_expected_context(self):
        response = self.client.get(self.url)

        assert 200 == response.status_code
        self.assertTemplateUsed(response, "core/dataset_files_list.html")
        assert settings.TEMPLATE_STRING_IF_INVALID not in response.content.decode()
        assert self.dataset == response.context["dataset"]
        assert self.table.version.collected_at == response.context["capture_date"]
        assert self.dataset.all_files == response.context["file_list"]

    def test_redirect_to_version_download_url_if_no_table_files(self):
        TableFile.objects.all().delete()

        expected_url = self.dataset.get_last_version().download_url
        response = self.client.get(self.url)

        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

    def test_404_if_dataset_does_not_exist(self):
        self.url = reverse("core:dataset-files-detail", args=["foo"])
        response = self.client.get(self.url)
        assert 404 == response.status_code

    def test_return_empty_list_if_no_visible_table(self):
        #  If the table is hidden, it can't be seen by the view under test
        self.table.hidden = True
        self.table.save()

        response = self.client.get(self.url)

        assert 200 == response.status_code
        self.assertTemplateUsed(response, "404.html")
        assert settings.TEMPLATE_STRING_IF_INVALID not in response.content.decode()
        assert response.context["message"]
