from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from model_bakery import baker

from core.models import TableFile
from core.tests.utils import BaseTestCaseWithSampleDataset
from traffic_control.tests.util import TrafficControlClient
from utils.tests import DjangoAssertionsMixin


class SampleDatasetDetailView(DjangoAssertionsMixin, BaseTestCaseWithSampleDataset):
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

    def create_user(self):
        self.username, self.password = "testuser", "supersecret"
        User = get_user_model()
        user = User.objects.create(username=self.username, is_active=True)
        user.set_password(self.password)
        user.save()

    def login(self):
        return self.client.login(username=self.username, password=self.password)

    def setUp(self):
        self.url = reverse("core:dataset-table-detail", args=["sample", "sample_table"])
        call_command("clear_cache")

        self.create_user()

    def test_display_dataset_table_data_with_expected_template(self):
        response = self.client.get(self.url)
        assert 200 == response.status_code
        self.assertTemplateUsed(response, "core/dataset-table-detail.html")
        assert "" == response.context["search_term"]

    def test_list_table_data_in_context_as_expected(self):
        data = baker.make(self.TableModel, _quantity=10)

        response = self.client.get(self.url)
        context = response.context

        assert 200 == response.status_code
        assert 10 == len(context["data"].paginator.object_list)
        assert all(d in context["data"].paginator.object_list for d in data)

    def test_apply_frontend_filter(self):
        self.login()

        match = baker.make(self.TableModel, sample_field="bar")
        baker.make(self.TableModel, sample_field="foo")
        baker.make(self.TableModel, sample_field="other")

        url = self.url + "?sample_field=bar"
        response = self.client.get(url)
        context = response.context

        assert 200 == response.status_code
        assert 1 == len(context["data"].paginator.object_list)
        assert match in context["data"].paginator.object_list

    @override_settings(RATELIMIT_ENABLE=True)
    @override_settings(RATELIMIT_RATE="0/s")
    @patch("traffic_control.decorators.ratelimit")
    def test_enforce_rate_limit_if_flagged(self, mocked_ratelimit):
        response = self.client.get(self.url)
        assert 429 == response.status_code
        self.assertTemplateUsed(response, "4xx.html")
        assert "Você atingiu o limite de requisições" in response.context["message"]
        assert 429 == response.context["title_4xx"]
        assert mocked_ratelimit.called is False  # this ensures the middleware is the one raising the 429 error

    @override_settings(RATELIMIT_ENABLE=True)
    @override_settings(RATELIMIT_RATE="0/s")
    @patch("traffic_control.decorators.ratelimit")
    def test_enforce_rate_limit_if_flagged_for_api(self, mocked_ratelimit):
        settings.ALLOWED_HOSTS.append(settings.BRASILIO_API_HOST)
        urlconf = settings.API_ROOT_URLCONF
        self.url = reverse("v1:dataset-table-data", args=["sample", "sample_table"], urlconf=urlconf)
        response = self.client.get(self.url, HTTP_HOST=settings.BRASILIO_API_HOST)
        content = response.json()
        assert 429 == response.status_code
        assert content["message"]


class TestDatasetFilesDetailView(DjangoAssertionsMixin, BaseTestCaseWithSampleDataset):
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
        assert response.context["message"]
