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

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=["warning"]))
    def test_import_data_from_a_valid_state_spreadsheet_request(self):
        # XXX: not sure if it is working.
        expected_response = {
            "warnings": ["warning 1", "warning 2"],
            "detail_url": "https://brasil.io/covid19/dataset/RJ"
        }

        expected_status = 200

        reverse_name = "covid19:statespreadsheet-list"
        self.url = reverse(reverse_name, args=["RJ"])

        response = self.client.post(self.url, data=self.data, format='json')

        assert expected_status == response.status_code
        #assert expected_response == response.json()
        assert {
                'date': '2020-05-20',
                'boletim_urls': ['http://google.com', 'http://brasil.io'],
                'boletim_notes': 'notes',
                'file': [
                    'municipio,confirmados,mortes\r\n',
                    'TOTAL NO ESTADO,102,32\r\n',
                    'Importados/Indefinidos,2,2\r\n',
                    'Abatiá,9,1\r\n',
                    'Adrianópolis,11,2\r\n',
                    'Agudos do Sul,12,3\r\n',
                    'Almirante Tamandaré,8,4\r\n',
                    'Altamira do Paraná,13,5\r\n',
                    'Alto Paraíso,47,15\r\n'
                ]
            } == response.json()

    def test_login_required(self):
        expected_status = 403
        reverse_name = "covid19:statespreadsheet-list"

        self.url = reverse(reverse_name, args=["RJ"])

        self.client.force_authenticate(user=None)

        response = self.client.post(self.url, data=self.data, format='json')
        assert expected_status == response.status_code
