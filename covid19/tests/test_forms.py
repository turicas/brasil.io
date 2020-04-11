import pytest
import shutil
from datetime import date
from localflavor.br.br_states import STATE_CHOICES
from model_bakery import baker
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Permission, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.test import TestCase

from covid19.forms import state_choices_for_user, StateSpreadsheetForm
from covid19.models import StateSpreadsheet


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
        self.data = {
            'date': date.today(),
            'state': 'RJ',
            'boletim_urls': 'http://google.com,http://brasil.io',
            'boletim_notes': 'notes',
        }
        self.file_data = {
            'file': self.gen_file('sample.csv', 'col1,col2'),
        }
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.user.groups.add(Group.objects.get(name__endswith='Rio de Janeiro'))

    def gen_file(self, name, content):
        if isinstance(content, str):
            content = str.encode(content)
        return SimpleUploadedFile(name, content)

    def tearDown(self):
        if Path(settings.MEDIA_ROOT).exists():
            shutil.rmtree(settings.MEDIA_ROOT)

    def test_form_requires_user_on_init(self):
        with pytest.raises(TypeError):
            StateSpreadsheetForm({})

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
        assert 'RJ' == spreadsheet.state
        assert spreadsheet.file
        assert ['http://google.com', 'http://brasil.io'] == spreadsheet.boletim_urls
        assert 'notes' == spreadsheet.boletim_notes
        assert StateSpreadsheet.UPLOADED == spreadsheet.status
        assert spreadsheet.cancelled is False
