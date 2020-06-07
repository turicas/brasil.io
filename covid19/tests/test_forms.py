import shutil
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import rows
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.test import TestCase
from localflavor.br.br_states import STATE_CHOICES
from model_bakery import baker

from covid19.exceptions import SpreadsheetValidationErrors
from covid19.forms import StateSpreadsheetForm, state_choices_for_user
from covid19.models import StateSpreadsheet
from covid19.tests.utils import Covid19DatasetTestCase

SAMPLE_SPREADSHEETS_DATA_DIR = Path(settings.BASE_DIR).joinpath("covid19", "tests", "data")


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
        covid_perms = Permission.objects.filter(codename__startswith=settings.COVID_IMPORT_PERMISSION_PREFIX)
        assert covid_perms.count() == 27  # this test requires migrations
        perm_1, perm_2 = covid_perms.filter(Q(codename__endswith="SP") | Q(codename__endswith="RJ"))
        self.user.groups.add(perm_1.group_set.get())
        self.user.groups.add(perm_2.group_set.get())

        choices = state_choices_for_user(self.user)

        assert 2 == len(choices)
        assert ("RJ", "Rio de Janeiro") in choices
        assert ("SP", "São Paulo") in choices


class StateSpreadsheetFormTests(Covid19DatasetTestCase):
    def setUp(self):
        valid_csv = SAMPLE_SPREADSHEETS_DATA_DIR / "sample-PR.csv"
        assert valid_csv.exists()

        self.data = {
            "date": date.today(),
            "state": "PR",
            "boletim_urls": "http://google.com\r\n\r http://brasil.io",
            "boletim_notes": "notes",
        }
        self.file_data = {"file": self.gen_file("sample.csv", valid_csv.read_bytes())}
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

    def test_required_fields(self):
        required_fields = ["date", "state", "file", "boletim_urls"]

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
        assert "PR" == spreadsheet.state
        assert spreadsheet.file
        assert ["http://google.com", "http://brasil.io"] == spreadsheet.boletim_urls
        assert "notes" == spreadsheet.boletim_notes
        assert StateSpreadsheet.UPLOADED == spreadsheet.status
        assert spreadsheet.cancelled is False
        assert len(spreadsheet.data) > 0
        assert len(spreadsheet.table_data) == 8  # total, undefined + 6 cities

    def test_invalidate_form_if_user_does_not_have_permission_to_the_state(self):
        self.data["state"] = "SP"

        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)

        assert not form.is_valid()
        assert "state" in form.errors

    def test_invalidate_if_future_date(self):
        self.data["date"] = date.today() + timedelta(days=1)

        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)

        assert not form.is_valid()
        assert "date" in form.errors

    def test_invalidate_form_if_any_invalid_url(self):
        self.data["boletim_urls"] = "xpto"

        form = StateSpreadsheetForm(self.data, self.file_data)

        assert not form.is_valid()
        assert "boletim_urls" in form.errors

    @patch("covid19.forms.rows.import_from_csv", Mock(return_value={}))
    @patch("covid19.forms.rows.import_from_xls", Mock(return_value={}))
    @patch("covid19.forms.rows.import_from_xlsx", Mock(return_value={}))
    @patch("covid19.forms.rows.import_from_ods", Mock(return_value={}))
    @patch("covid19.forms.format_spreadsheet_rows_as_dict", Mock(return_value=([], [])))
    def test_invalidate_if_wrong_file_format(self):
        valid_formats = ["csv", "xls", "xlsx", "ods"]
        for format in valid_formats:
            self.file_data["file"] = self.gen_file(f"sample.{format}", "col1,col2")

            form = StateSpreadsheetForm(self.data, self.file_data)
            assert form.is_valid(), form.errors

        self.file_data["file"] = self.gen_file("sample.txt", "col1,col2")
        form = StateSpreadsheetForm(self.data, self.file_data)
        assert "__all__" in form.errors

    @patch("covid19.forms.format_spreadsheet_rows_as_dict", autospec=True)
    def test_populate_object_data_with_valid_sample(self, mocked_format):
        mocked_format.return_value = (["results", "list"], ["warnings", "list"])
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)
        assert form.is_valid(), form.errors
        expected = {
            "table": ["results", "list"],
            "errors": [],
            "warnings": ["warnings", "list"],
        }

        spreadsheet = form.save()
        spreadsheet.refresh_from_db()

        assert expected == spreadsheet.data
        assert 1 == mocked_format.call_count
        method_call = mocked_format.call_args_list[0]
        data, import_date, state = method_call[0]
        kwargs = method_call[1]
        assert date.today() == import_date
        assert state == "PR"
        for entry, expected_entry in zip(data, rows.import_from_csv(self.file_data["file"])):
            assert entry._asdict() == expected_entry._asdict()
        assert not kwargs["skip_sum_cases"]
        assert not kwargs["skip_sum_deaths"]

    @patch("covid19.forms.format_spreadsheet_rows_as_dict", autospec=True)
    def test_skip_sum_validations_if_flagged_in_the_form_data(self, mocked_format):
        mocked_format.return_value = (["results", "list"], ["warnings", "list"])
        self.data.update(
            {"skip_sum_cases": True, "skip_sum_deaths": True,}
        )
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)
        assert form.is_valid(), form.errors
        expected = {
            "table": ["results", "list"],
            "errors": [],
            "warnings": ["warnings", "list"],
        }

        spreadsheet = form.save()
        spreadsheet.refresh_from_db()

        assert expected == spreadsheet.data
        assert 1 == mocked_format.call_count
        method_call = mocked_format.call_args_list[0]
        data, import_date, state = method_call[0]
        kwargs = method_call[1]
        assert date.today() == import_date
        assert state == "PR"
        for entry, expected_entry in zip(data, rows.import_from_csv(self.file_data["file"])):
            assert entry._asdict() == expected_entry._asdict()
        assert kwargs["skip_sum_cases"] is True
        assert kwargs["skip_sum_deaths"] is True

    @patch("covid19.forms.format_spreadsheet_rows_as_dict", autospec=True)
    def test_list_all_errors_fom_the_import_process(self, mocked_format):
        exception = SpreadsheetValidationErrors()
        exception.new_error("Error 1")
        exception.new_error("Error 2")
        mocked_format.side_effect = exception

        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)
        assert not form.is_valid()

        assert 2 == len(form.errors["__all__"])
        assert "Error 1" in form.errors["__all__"]
        assert "Error 2" in form.errors["__all__"]

    def test_import_data_from_xls_with_sucess(self):
        valid_xls = SAMPLE_SPREADSHEETS_DATA_DIR / "sample-PR.xls"
        assert valid_xls.exists()

        self.file_data["file"] = self.gen_file("sample.xls", valid_xls.read_bytes())
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)

        assert form.is_valid(), form.errors

    def test_import_data_from_xlsx_with_sucess(self):
        valid_xlsx = SAMPLE_SPREADSHEETS_DATA_DIR / "sample-PR.xlsx"
        assert valid_xlsx.exists()

        self.file_data["file"] = self.gen_file("sample.xlsx", valid_xlsx.read_bytes())
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)

        assert form.is_valid(), form.errors

    def test_import_data_from_ods_with_sucess(self):
        valid_ods = SAMPLE_SPREADSHEETS_DATA_DIR / "sample-PR.ods"
        assert valid_ods.exists()

        self.file_data["file"] = self.gen_file("sample.ods", valid_ods.read_bytes())
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)

        assert form.is_valid(), form.errors

    def test_raise_validation_error_if_any_error_with_rows_import_functions(self):
        valid_xls = SAMPLE_SPREADSHEETS_DATA_DIR / "sample-PR.xls"
        assert valid_xls.exists()

        # wrong file extension
        self.file_data["file"] = self.gen_file("sample.csv", valid_xls.read_bytes())
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)

        assert not form.is_valid()
        assert "__all__" in form.errors

    def test_validate_notes_max_length(self):
        self.data["boletim_notes"] = "a" * 2001
        form = StateSpreadsheetForm(self.data, self.file_data, user=self.user)
        assert not form.is_valid()
        assert "boletim_notes" in form.errors
