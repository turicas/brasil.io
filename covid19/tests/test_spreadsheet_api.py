import shutil
from unittest.mock import patch, Mock
from datetime import date, timedelta
from pathlib import Path
from model_bakery import baker
import requests
from urllib import request  # to build absolute url.

from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.views.decorators.csrf import ensure_csrf_cookie
from django.test import Client
from rest_framework.test import APITestCase
from rest_framework.test import force_authenticate, RequestsClient
from rest_framework.authtoken.models import Token

from covid19.exceptions import SpreadsheetValidationErrors


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

        self.file_data = self.gen_file(self.filename, valid_csv.read_bytes())
        self.data['file'] = self.file_data
        self.setUp_user_credentials()

    def setUp_user_credentials(self):
        self.user = baker.make(get_user_model())
        self.user.groups.add(Group.objects.get(name__endswith="Rio de Janeiro"))
        self.user.groups.add(Group.objects.get(name__endswith="Paraná"))

        self.token = baker.make(Token, user=self.user)
        self.headers = {'Authorization': f'Token {self.token.key}'}
        self.client.credentials(HTTP_AUTHORIZATION=self.headers['Authorization'])
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
        expected_response = {
            'errors': ["error 1", "error 2"]
        }
        expected_status = 400

        exception = SpreadsheetValidationErrors()
        exception.new_error("error 1")
        exception.new_error("error 2")
        mock_merge.side_effect = exception

        tomorrow = date.today() + timedelta(days=1)
        tomorrow = tomorrow.isoformat()
        self.data['date'] = tomorrow

        reverse_name = "covid19:statespreadsheet-list"

        self.url = reverse(reverse_name, args=["RJ"])

        breakpoint()
        response = self.client.post(self.url, data=self.data)

        assert len(exception.errors) == 2
        assert expected_status == response.status_code
        assert expected_response == response.json()

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=["warning"]))
    def test_import_data_from_a_valid_state_spreadsheet_request(self):
        expected_response = {
            "warnings": ["warning 1", "warning 2"],
            "detail_url": "https://brasil.io/covid19/dataset/RJ"
        }

        expected_status = 200

        reverse_name = "covid19:statespreadsheet-list"
        self.url = reverse(reverse_name, args=["RJ"])

        response = self.client.post(self.url, data=self.data)

        assert expected_status == response.status_code
        assert expected_response == response.json()

    def test_login_required(self):
        expected_status = 403
        reverse_name = "covid19:statespreadsheet-list"

        self.url = reverse(reverse_name, args=["RJ"])

        self.client.credentials()
        response = self.client.post(self.url, data=self.data)
        assert expected_status == response.status_code
