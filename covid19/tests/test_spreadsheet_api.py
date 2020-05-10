import shutil
import io
from unittest.mock import patch, Mock
from datetime import date, timedelta
from pathlib import Path
from model_bakery import baker

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import login
from rest_framework.test import APITestCase

from covid19.exceptions import SpreadsheetValidationErrors
from covid19.forms import StateSpreadsheetForm


class ImportSpreadsheetByDateAPIViewTests(APITestCase):
    def setUp(self):
        valid_csv = settings.SAMPLE_SPREADSHEETS_DATA_DIR / "sample-PR.csv"
        assert valid_csv.exists()

        self.data = {
            "date": date.today(),
            "boletim_urls": ["http://google.com", "http://brasil.io"],
            "boletim_notes": "notes",
        }

        self.filename = f'sample.csv'
        
        self.file_data = {"file": self.gen_file(self.filename, valid_csv.read_bytes())}
        self.data['file'] = self.file_data

        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.user.groups.add(Group.objects.get(name__endswith="Rio de Janeiro"))
        self.user.groups.add(Group.objects.get(name__endswith="Paraná"))

        self.client.force_login(user=self.user)

    def gen_file(self, name, content):
        if isinstance(content, str):
            content = str.encode(content)
        return SimpleUploadedFile(name, content)

    def tearDown(self):
        if Path(settings.MEDIA_ROOT).exists():
            shutil.rmtree(settings.MEDIA_ROOT)

    @patch("covid19.forms.format_spreadsheet_rows_as_dict", autospec=True)
    def test_400_if_spreadsheet_error_on_import_data(self, mock_merge):
        exception = SpreadsheetValidationErrors()
        exception.new_error("error 1")
        exception.new_error("error 2")
        mock_merge.side_effect = exception

        tomorrow = date.today() + timedelta(days=1)
        tomorrow = tomorrow.isoformat()
        self.data['date'] = tomorrow

        reverse_name = "covid19:statespreadsheet-list"

        self.url = reverse(reverse_name, args=["RJ"])

        response = self.client.post(self.url, data=self.data, format='json')

        assert len(exception.errors) == 2
        assert 400 == response.status_code
        assert {
                'errors': ["error 1", "error 2"]
                } == response.json()

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=["warning"]))
    def test_import_data_from_a_valid_state_spreadsheet_request(self):
        reverse_name = "covid19:statespreadsheet-list"

        self.url = reverse(reverse_name, args=["RJ"])

        response = self.client.get(reverse('covid19:dashboard'))
        assert response.status_code == 200
        csrftoken = response.cookies['csrftoken']

        response = self.client.post(self.url, data=self.data, format='json', headers={'X-CSRFToken': csrftoken})

        assert 200 == response.status_code
        assert {
                "warnings": ["warning 1", "warning 2"],
                "detail_url": "https://brasil.io/covid19/dataset/RJ"
                } == response.json()

    def test_login_required(self):
        reverse_name = "covid19:statespreadsheet-list"

        self.url = reverse(reverse_name, args=["RJ"])

        self.client.logout()
        response = self.client.post(self.url, self.data, format='json')
        assert 403 == response.status_code
