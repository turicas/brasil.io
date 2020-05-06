import shutil
import io
from unittest.mock import patch
from datetime import date, timedelta
from pathlib import Path
from model_bakery import baker

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission, Group
from django.core.files.uploadedfile import SimpleUploadedFile

from covid19.exceptions import SpreadsheetValidationErrors
from covid19.forms import StateSpreadsheetForm
from covid19.tests.utils import Covid19DatasetTestCase

SAMPLE_SPREADSHEETS_DATA_DIR = Path(settings.BASE_DIR).joinpath("covid19", "tests", "data")


class ImportSpreadsheetByDateAPIViewTests(Covid19DatasetTestCase):
    def setUp(self):
        valid_csv = SAMPLE_SPREADSHEETS_DATA_DIR / "sample-PR.csv"
        assert valid_csv.exists()

        self.data = {
            "date": date.today(),
            "state": "PR",
            "boletim_urls": "http://google.com\r\n\r http://brasil.io",
            "boletim_notes": "notes",
        }
        self.file_data = {"file": self.gen_file(f"sample.csv", valid_csv.read_bytes())}
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.user.groups.add(Group.objects.get(name__endswith="Rio de Janeiro"))
        self.user.groups.add(Group.objects.get(name__endswith="Paraná"))

    def gen_file(self, name, content):
        if isinstance(content, str):
            content = str.encode(content)
        return SimpleUploadedFile(name, content)

    def tearDown(self):
        if Path(settings.MEDIA_ROOT).exists():
            shutil.rmtree(settings.MEDIA_ROOT)

    @patch("covid19.views.StateSpreadsheetViewList.post", autospec=True)
    def test_400_if_spreadsheet_error_on_import_data(self, mock_merge):
        exception = SpreadsheetValidationErrors()
        exception.new_error("error 1")
        exception.new_error("error 2")
        mock_merge.side_effect = exception

        reverse_name = "covid19:statespreadsheet-list"

        tomorrow = date.today() + timedelta(days=1)
        tomorrow = tomorrow.isoformat()
        self.url = reverse(reverse_name, args=["RJ", f"{tomorrow}"])

        response = self.client.post(self.url, data=self.data)

        assert len(exception.errors) == 2
        assert 400 == response.status_code
        assert {
                'success': False,
                'errors': ["error 1", "error 2"]
                } == response.json()

    def test_import_data_from_a_valid_state_spreadsheet_request(self):
        reverse_name = "covid19:statespreadsheet-list"

        self.url = reverse(reverse_name, args=["RJ", "2020-05-04"])

        response = self.client.post(self.url, data=self.data)

        assert len(response.json()['errors']) == 0
        assert 200 == response.status_code
        assert {
                'success': True,
                'errors': []
                } == response.json()
