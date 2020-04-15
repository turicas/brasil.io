import shutil
from datetime import date
from localflavor.br.br_states import STATE_CHOICES
from model_bakery import baker
from pathlib import Path
from unittest.mock import patch, Mock

from django.conf import settings
from django.contrib.auth.models import Permission, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.test import TestCase

from covid19.forms import state_choices_for_user, StateSpreadsheetForm
from covid19.models import StateSpreadsheet


SAMPLE_SPREADSHEETS_DATA_DIR = Path(settings.BASE_DIR).joinpath('covid19', 'tests', 'data')


class AvailableStatesForUserTests(TestCase):

    def setUp(self):
        self.user = baker.make(settings.AUTH_USER_MODEL)

    def test_super_user_can_acccess_all_states(self):
        self.user.is_superuser = True

        choices = state_choices_for_user(self.user)

        assert list(STATE_CHOICES) == choices

    def test_user_without_permissions_has_no_choices(self):
        choices = state_choices_for_user(self.user)

        assert [] == choices

    def test_return_choices_from_user_permissions(self):
        covid_perms = Permission.objects.filter(
            codename__startswith=settings.COVID_IMPORT_PERMISSION_PREFIX
        )
        assert covid_perms.count() == 27  # this test requires migrations
        perm_1, perm_2 = covid_perms.filter(Q(codename__endswith='SP') | Q(codename__endswith='RJ'))
        self.user.groups.add(perm_1.group_set.get())
        self.user.groups.add(perm_2.group_set.get())

        choices = state_choices_for_user(self.user)

        assert 2 == len(choices)
        assert ('RJ', 'Rio de Janeiro') in choices
        assert ('SP', 'São Paulo') in choices


class StateSpreadsheetFormTests(TestCase):

    def setUp(self):
        valid_csv = SAMPLE_SPREADSHEETS_DATA_DIR / 'sample-PR.csv'
        assert valid_csv.exists()

        self.data = {
            'date': date.today(),
            'state': 'PR',
            'boletim_urls': 'http://google.com\nhttp://brasil.io',
            'boletim_notes': 'notes',
        }
        self.file_data = {
            'file': self.gen_file(f'sample.csv', valid_csv.read_bytes())
        }
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.user.groups.add(Group.objects.get(name__endswith='Rio de Janeiro'))
        self.user.groups.add(Group.objects.get(name__endswith='Paraná'))

    def gen_file(self, name, content):
        if isinstance(content, str):
            content = str.encode(content)
        return SimpleUploadedFile(name, content)

    def tearDown(self):
        if Path(settings.MEDIA_ROOT).exists():
            shutil.rmtree(settings.MEDIA_ROOT)

    def test_required_fields(self):
        required_fields = ['date', 'state', 'file', 'boletim_urls']

        form = StateSpreadsheetForm({}, user=self.user)

        assert not form.is_valid()
        assert len(required_fields) == len(form.errors)
        for field in required_fields:
            assert field in form.errors

    def test_create_new_spreadsheet_with_valid_data(self):
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)
        assert form.is_valid(), form.errors

        spreadsheet = form.save()
        spreadsheet.refresh_from_db()

        assert self.user == spreadsheet.user
        assert date.today() == spreadsheet.date
        assert 'PR' == spreadsheet.state
        assert spreadsheet.file
        assert ['http://google.com', 'http://brasil.io'] == spreadsheet.boletim_urls
        assert 'notes' == spreadsheet.boletim_notes
        assert StateSpreadsheet.UPLOADED == spreadsheet.status
        assert spreadsheet.cancelled is False

    def test_invalidate_form_if_user_does_not_have_permission_to_the_state(self):
        self.data['state'] = 'SP'

        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)

        assert not form.is_valid()
        assert 'state' in form.errors

    def test_invalidate_form_if_any_invalid_url(self):
        self.data['boletim_urls'] = 'xpto'

        form = StateSpreadsheetForm(self.data, self.file_data)

        assert not form.is_valid()
        assert 'boletim_urls' in form.errors

    @patch('covid19.forms.rows.import_from_csv', Mock(return_value={}))
    @patch('covid19.forms.rows.import_from_xls', Mock(return_value={}))
    @patch('covid19.forms.rows.import_from_xlsx', Mock(return_value={}))
    @patch('covid19.forms.rows.import_from_ods', Mock(return_value={}))
    @patch('covid19.forms.format_spreadsheet_rows_as_dict', Mock())
    def test_invalidate_if_wrong_file_format(self):
        valid_formats = ['csv', 'xls', 'xlsx', 'ods']
        for format in valid_formats:
            self.file_data['file'] = self.gen_file(f'sample.{format}', 'col1,col2')

            form = StateSpreadsheetForm(self.data, self.file_data)
            assert form.is_valid(), form.errors

        self.file_data['file'] = self.gen_file(f'sample.txt', 'col1,col2')
        form = StateSpreadsheetForm(self.data, self.file_data)
        assert '__all__' in form.errors

    def test_populate_object_data_with_valid_sample(self):
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)
        assert form.is_valid(), form.errors
        expected = {
            "table": {
                'total': {'confirmados': 100, 'mortes': 30},
                'importados_indefinidos': {'confirmados': 2, 'mortes': 2},
                'cidades': {
                    'Abatiá': {'confirmados': 9, 'mortes': 1},
                    'Adrianópolis': {'confirmados': 11, 'mortes': 2},
                    'Agudos do Sul': {'confirmados': 12, 'mortes': 3},
                    'Almirante Tamandaré': {'confirmados': 8, 'mortes': 4},
                    'Altamira do Paraná': {'confirmados': 13, 'mortes': 5},
                    'Alto Paraíso': {'confirmados': 47, 'mortes': 15},
                }
            },
            "errors": [],
            "warnings": [],
        }

        spreadsheet = form.save()
        spreadsheet.refresh_from_db()

        assert expected == spreadsheet.data

    def test_import_data_from_xls_with_sucess(self):
        valid_xls = SAMPLE_SPREADSHEETS_DATA_DIR / 'sample-PR.xls'
        assert valid_xls.exists()

        self.file_data['file'] = self.gen_file(f'sample.xls', valid_xls.read_bytes())
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)

        assert form.is_valid(), form.errors

    def test_import_data_from_xlsx_with_sucess(self):
        valid_xlsx = SAMPLE_SPREADSHEETS_DATA_DIR / 'sample-PR.xlsx'
        assert valid_xlsx.exists()

        self.file_data['file'] = self.gen_file(f'sample.xlsx', valid_xlsx.read_bytes())
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)

        assert form.is_valid(), form.errors

    def test_import_data_from_ods_with_sucess(self):
        valid_ods = SAMPLE_SPREADSHEETS_DATA_DIR / 'sample-PR.ods'
        assert valid_ods.exists()

        self.file_data['file'] = self.gen_file(f'sample.ods', valid_ods.read_bytes())
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)

        assert form.is_valid(), form.errors

    def test_raise_validation_error_if_any_error_with_rows_import_functions(self):
        valid_xls = SAMPLE_SPREADSHEETS_DATA_DIR / 'sample-PR.xls'
        assert valid_xls.exists()

        # wrong file extension
        self.file_data['file'] = self.gen_file(f'sample.csv', valid_xls.read_bytes())
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)

        assert not form.is_valid()
        assert '__all__' in form.errors
