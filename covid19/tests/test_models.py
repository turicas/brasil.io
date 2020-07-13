import json
import shutil
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import TestCase
from model_bakery import baker

from covid19.exceptions import OnlyOneSpreadsheetException
from covid19.models import StateSpreadsheet
from covid19.signals import new_spreadsheet_imported_signal


class StateSpreadsheetTests(TestCase):
    def setUp(self):
        data = date.today().isoformat()
        self.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 12,
                "date": data,
                "deaths": 7,
                "place_type": "state",
                "state": "PR",
            },
            {
                "city": "Importados/Indefinidos",
                "city_ibge_code": None,
                "confirmed": 2,
                "date": data,
                "deaths": 2,
                "place_type": "city",
                "state": "PR",
            },
            {
                "city": "Curitiba",
                "city_ibge_code": 4321,
                "confirmed": 10,
                "date": data,
                "deaths": 5,
                "place_type": "city",
                "state": "PR",
            },
        ]

    def tearDown(self):
        if Path(settings.MEDIA_ROOT).exists():
            shutil.rmtree(settings.MEDIA_ROOT)

    def test_format_filename_to_add_uf_date_username(self):
        today = date.today()

        spreadsheet = baker.make(
            StateSpreadsheet,
            user__username="foo",
            state="rj",
            date=today,
            _create_files=True,  # will create a dummy .txt file
        )
        expected = f"{settings.MEDIA_ROOT}/covid19/RJ/casos-RJ-{today.isoformat()}-foo-1.txt"

        assert expected == spreadsheet.file.path

    def test_format_filename_counting_previous_uploads_from_user(self):
        today = date.today()
        user = baker.make(settings.AUTH_USER_MODEL, username="foo")
        state = "rj"
        prev_qtd = 4
        baker.make(StateSpreadsheet, user=user, state=state, date=today, _quantity=prev_qtd)
        baker.make(  # other state, same date
            StateSpreadsheet, user=user, state="sp", date=today,
        )
        baker.make(  # other date, same state
            StateSpreadsheet, user=user, state=state, date=today + timedelta(days=1),
        )
        baker.make(  # same date, same state, other user
            StateSpreadsheet, user__username="new_user", state=state, date=today,
        )

        spreadsheet = baker.make(StateSpreadsheet, user=user, state=state, date=today, _create_files=True)
        expected = f"{settings.MEDIA_ROOT}/covid19/RJ/casos-RJ-{today.isoformat()}-foo-5.txt"

        assert expected == spreadsheet.file.path

    def test_filter_older_versions_exclude_the_object_if_id(self):
        kwargs = {
            "date": date.today(),
            "user": baker.make(settings.AUTH_USER_MODEL),
            "state": "rj",
        }
        baker.make(StateSpreadsheet, _quantity=3, **kwargs)

        spreadsheet = baker.prepare(StateSpreadsheet, **kwargs)
        assert 3 == StateSpreadsheet.objects.filter_older_versions(spreadsheet).count()

        spreadsheet.save()
        spreadsheet.refresh_from_db()
        assert 3 == StateSpreadsheet.objects.filter_older_versions(spreadsheet).count()

    @patch("covid19.signals.process_new_spreadsheet_task", autospec=True)
    def test_cancel_previous_imports_from_user_for_same_state_and_data(self, mocked_process_new_spreadsheet):
        kwargs = {
            "date": date.today(),
            "user": baker.make(settings.AUTH_USER_MODEL),
            "state": "RJ",
        }

        previous = baker.make(StateSpreadsheet, _quantity=3, **kwargs)
        assert all([not p.cancelled for p in previous])

        spreadsheet = baker.make(StateSpreadsheet, **kwargs)
        new_spreadsheet_imported_signal.send(sender=self, spreadsheet=spreadsheet)
        spreadsheet.refresh_from_db()
        assert not spreadsheet.cancelled

        for prev in previous:
            prev.refresh_from_db()
            assert prev.cancelled

        mocked_process_new_spreadsheet.delay.assert_called_once_with(spreadsheet_pk=spreadsheet.pk)

    def test_compare_matching_spreadsheets_with_success(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state="PR", _quantity=2)
        sp1.table_data = deepcopy(self.table_data)
        sp2.table_data = deepcopy(self.table_data)

        assert [] == sp1.compare_to_spreadsheet(sp2)

    def test_compare_error_if_not_from_same_state(self):
        sp1 = baker.make(StateSpreadsheet, date=date.today(), state="RJ")
        sp2 = baker.make(StateSpreadsheet, date=date.today(), state="PR")

        sp1.table_data = deepcopy(self.table_data)
        sp2.table_data = deepcopy(self.table_data)

        assert ["Estados das planilhas são diferentes."] == sp1.compare_to_spreadsheet(sp2)

    def test_compare_error_if_not_from_date(self):
        yesterday = date.today() - timedelta(days=1)
        sp1 = baker.make(StateSpreadsheet, date=yesterday, state="PR")
        sp2 = baker.make(StateSpreadsheet, date=date.today(), state="PR")

        sp1.table_data = deepcopy(self.table_data)
        sp2.table_data = deepcopy(self.table_data)

        assert ["Datas das planilhas são diferentes."] == sp1.compare_to_spreadsheet(sp2)

    def test_error_if_mismatch_of_total_numbers(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state="PR", _quantity=2)
        sp1.table_data = deepcopy(self.table_data)

        self.table_data[0]["deaths"] = 0
        sp2.table_data = self.table_data
        expected = ["Número de casos confirmados ou óbitos diferem para Total."]

        assert expected == sp1.compare_to_spreadsheet(sp2)

    def test_error_if_mismatch_of_city_numbers(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state="PR", _quantity=2)
        sp1.table_data = deepcopy(self.table_data)

        self.table_data[1]["deaths"] = 0
        self.table_data[2]["confirmed"] = 0
        sp2.table_data = self.table_data
        expected = [
            "Número de casos confirmados ou óbitos diferem para Importados/Indefinidos.",
            "Número de casos confirmados ou óbitos diferem para Curitiba.",
        ]

        assert sorted(expected) == sorted(sp1.compare_to_spreadsheet(sp2))

    def test_error_if_mismatch_because_other_cities_does_not_exist(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state="PR", _quantity=2)

        sp1.table_data = self.table_data
        expected = [
            "Número de casos confirmados ou óbitos diferem para Total.",
            f"Importados/Indefinidos está na planilha (por {sp1.user.username}) mas não na outra usada para a comparação (por {sp2.user.username}).",  # noqa
            f"Curitiba está na planilha (por {sp1.user.username}) mas não na outra usada para a comparação (por {sp2.user.username}).",  # noqa
        ]

        assert sorted(expected) == sorted(sp1.compare_to_spreadsheet(sp2))

    def test_error_if_mismatch_because_other_cities_exists_only_in_the_other_spreadsheet(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state="PR", _quantity=2)

        sp1.table_data = self.table_data[:-1]
        sp2.table_data = self.table_data
        expected = [
            f"Curitiba está na planilha usada para a comparação (por {sp2.user.username}) mas não na importada (por {sp1.user.username}).",  # noqa
        ]

        assert sorted(expected) == sorted(sp1.compare_to_spreadsheet(sp2))

    def test_link_to_matching_spreadsheet_peer_for_valid_spreadsheet(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state="PR", _quantity=2)
        sp1.table_data = deepcopy(self.table_data)
        sp1.save()
        sp2.table_data = deepcopy(self.table_data)
        sp2.save()

        assert (True, []) == sp1.link_to_matching_spreadsheet_peer()
        sp1.refresh_from_db()
        sp2.refresh_from_db()
        assert sp2 == sp1.peer_review
        assert sp1 == sp2.peer_review
        assert sp1.ready_to_import is True

    def test_link_to_matching_spreadsheet_peer_considers_previous_fails(self):
        user_1, user_2 = baker.make(settings.AUTH_USER_MODEL, _quantity=2)
        previous_sp1 = baker.prepare(StateSpreadsheet, date=date.today(), state="PR", user=user_1)
        previous_sp1.table_data = []
        previous_sp1.save()

        sp2 = baker.prepare(StateSpreadsheet, date=date.today(), state="PR", user=user_2)
        sp2.table_data = deepcopy(self.table_data)
        sp2.save()

        previous_sp1.link_to_matching_spreadsheet_peer()
        previous_sp1.refresh_from_db()
        sp2.refresh_from_db()

        assert previous_sp1.errors
        assert sp2.errors
        assert sp2.status == StateSpreadsheet.CHECK_FAILED
        assert previous_sp1.peer_review == sp2
        assert sp2.peer_review == previous_sp1

        sp1 = baker.prepare(StateSpreadsheet, date=date.today(), state="PR", user=user_1)
        sp1.table_data = deepcopy(self.table_data)
        sp1.save()

        assert (True, []) == sp1.link_to_matching_spreadsheet_peer()
        sp1.refresh_from_db()
        sp2.refresh_from_db()
        previous_sp1.refresh_from_db()
        assert sp2 == sp1.peer_review
        assert sp1 == sp2.peer_review
        assert previous_sp1.peer_review == sp1
        assert sp1.ready_to_import is True
        assert sp2.ready_to_import is True
        assert sp1.errors == []
        assert sp2.errors == []
        assert sp1.status == StateSpreadsheet.UPLOADED
        assert sp2.status == StateSpreadsheet.UPLOADED
        assert bool(previous_sp1.errors) is True

    def test_raise_exception_if_single_spreadsheet(self):
        sp1 = baker.make(StateSpreadsheet, date=date.today(), state="RJ")
        baker.make(StateSpreadsheet, date=date.today(), state="PR")

        with pytest.raises(OnlyOneSpreadsheetException):
            sp1.link_to_matching_spreadsheet_peer()

    def test_link_to_matching_spreadsheet_peer_for_not_matching_spreadsheets(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state="PR", _quantity=2)
        sp1.table_data = deepcopy(self.table_data)
        sp1.save()

        self.table_data[0]["deaths"] = 0
        sp2.table_data = self.table_data
        sp2.save()
        expected = ["Número de casos confirmados ou óbitos diferem para Total."]

        valid, errors = sp1.link_to_matching_spreadsheet_peer()
        sp1.refresh_from_db()
        sp2.refresh_from_db()

        assert not valid
        assert expected == errors
        assert expected == sp1.errors
        assert sp1.status == StateSpreadsheet.CHECK_FAILED
        assert expected == sp2.errors
        assert sp2.status == StateSpreadsheet.CHECK_FAILED

    def test_import_to_final_dataset_update_spreadsheet_status(self):
        spreadsheet = baker.make(StateSpreadsheet, _fill_optional=["peer_review"])
        assert StateSpreadsheet.UPLOADED == spreadsheet.status
        assert not StateSpreadsheet.objects.deployed().exists()

        spreadsheet.import_to_final_dataset()
        spreadsheet.refresh_from_db()

        assert StateSpreadsheet.DEPLOYED == spreadsheet.status
        assert StateSpreadsheet.DEPLOYED == spreadsheet.peer_review.status
        assert spreadsheet.automatically_created is False
        assert spreadsheet.peer_review in StateSpreadsheet.objects.deployed()

    def test_import_to_final_dataset_raise_error_if_invalid_status(self):
        spreadsheet = baker.make(StateSpreadsheet, status=StateSpreadsheet.CHECK_FAILED, _fill_optional=["peer_review"])
        with pytest.raises(ValueError):
            spreadsheet.import_to_final_dataset()

    def test_import_to_final_dataset_raise_error_if_cancelled(self):
        spreadsheet = baker.make(StateSpreadsheet, cancelled=True, _fill_optional=["peer_review"])
        with pytest.raises(ValueError):
            spreadsheet.import_to_final_dataset()

    def test_import_to_final_dataset_raise_error_if_no_peer_review(self):
        spreadsheet = baker.make(StateSpreadsheet)
        with pytest.raises(ValueError):
            spreadsheet.import_to_final_dataset()

    def test_notify_after_import(self):
        args = []

        def notification_func(spreadsheet):
            args.append(spreadsheet)

        spreadsheet = baker.make(StateSpreadsheet, _fill_optional=["peer_review"])
        spreadsheet.import_to_final_dataset(notification_func)

        assert [spreadsheet] == args

    def test_ready_to_import_from_state_return_single_spreadsheet_by_day(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        sp1, sp2 = baker.make(StateSpreadsheet, state="RJ", date=yesterday, _quantity=2)
        sp3, sp4 = baker.make(StateSpreadsheet, state="RJ", date=today, _quantity=2)
        sp1.peer_review = sp2
        sp2.peer_review = sp1
        sp3.peer_review = sp4
        sp4.peer_review = sp3
        sp1.save()
        sp2.save()
        sp3.save()
        sp4.save()
        assert all([s.ready_to_import for s in StateSpreadsheet.objects.all()])
        StateSpreadsheet.objects.all().update(status=StateSpreadsheet.DEPLOYED)
        baker.make(StateSpreadsheet, state="RJ", date=today, _quantity=2)  # other data not deployed

        deployables = StateSpreadsheet.objects.deployable_for_state("RJ")
        assert 2 == deployables.count()
        assert deployables[0] in [sp3, sp4]
        assert deployables[1] in [sp1, sp2]

        deployables = StateSpreadsheet.objects.deployable_for_state("RJ", avoid_peer_review_dupes=False)
        assert 4 == deployables.count()
        assert sp1 in deployables
        assert sp2 in deployables
        assert sp3 in deployables
        assert sp4 in deployables

    def test_pernambuco_mismatch_regression_test(self):
        """
        Esse erro aconteceu porque a planilha sp2 possuiu entradas duplicadas para Vicência.
        Esse teste garante que, mesmo que esse erro passe na validação individual da planilha,
        ele não prossiga na comparação com outras.
        """
        json_dir = settings.SAMPLE_SPREADSHEETS_DATA_DIR / "table_data"
        sp1 = baker.make(StateSpreadsheet, state="PE", date=date.today())
        sp2 = baker.make(StateSpreadsheet, state="PE", date=date.today())

        with open(json_dir / "PE_2020_05_03_planilha_1.json") as fd:
            sp1.table_data = json.load(fd)
            sp1.save()
            sp1.refresh_from_db()
        with open(json_dir / "PE_2020_05_03_planilha_2.json") as fd:
            sp2.table_data = json.load(fd)
            sp2.save()
            sp2.refresh_from_db()

        expected = [
            f"Número de entradas finais divergem. A planilha de comparação (por {sp2.user.username}) possui 143 mas a importada (por {sp1.user.username}) possui 142.",  # noqa
        ]
        assert sp1.compare_to_spreadsheet(sp2) == expected

        expected = [
            f"Número de entradas finais divergem. A planilha de comparação (por {sp1.user.username}) possui 142 mas a importada (por {sp2.user.username}) possui 143.",  # noqa
            "Número de casos confirmados ou óbitos diferem para Vicência.",
        ]
        assert sp2.compare_to_spreadsheet(sp1) == expected

    def test_import_to_final_dataset_automatically_created(self):
        spreadsheet = baker.make(StateSpreadsheet)
        assert StateSpreadsheet.UPLOADED == spreadsheet.status
        assert not StateSpreadsheet.objects.deployed().exists()

        spreadsheet.import_to_final_dataset(automatically_created=True)
        spreadsheet.refresh_from_db()

        assert StateSpreadsheet.DEPLOYED == spreadsheet.status
        assert StateSpreadsheet.DEPLOYED == spreadsheet.peer_review.status
        assert spreadsheet.automatically_created is True
        assert spreadsheet.peer_review in StateSpreadsheet.objects.deployed()
        assert spreadsheet.peer_review == spreadsheet


class StateSpreadsheetManagerTests(TestCase):
    def setUp(self):
        self.state = "PR"
        self.date = date.today()

    def assertDataEntry(self, cases, date, label, confirmed, deaths):
        assert date in cases, f"No cases for date {date}"
        assert label in cases[date], f"No entry for {label} on date {date}"
        assert {"confirmed": confirmed, "deaths": deaths} == cases[date][label]

    def test_get_report_data_from_state(self):
        sp = baker.make(
            StateSpreadsheet,
            boletim_urls=["https://brasil.io/", "https://saude.gov.br/"],
            boletim_notes="foo",
            status=StateSpreadsheet.DEPLOYED,
            state=self.state,
            date=self.date,
        )
        sp_date = self.date.isoformat()
        sp.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 12,
                "date": sp_date,
                "deaths": 7,
                "place_type": "state",
                "state": self.state,
            },
            {
                "city": "Importados/Indefinidos",
                "city_ibge_code": None,
                "confirmed": 2,
                "date": sp_date,
                "deaths": 2,
                "place_type": "city",
                "state": self.state,
            },
            {
                "city": "Curitiba",
                "city_ibge_code": 4321,
                "confirmed": 10,
                "date": sp_date,
                "deaths": 5,
                "place_type": "city",
                "state": self.state,
            },
        ]
        sp.save()

        report_data = StateSpreadsheet.objects.get_state_data("PR")
        reports, cases = report_data["reports"], report_data["cases"]

        assert 2 == len(reports)
        assert {"date": self.date, "url": "https://brasil.io/", "notes": "foo"} in reports
        assert {"date": self.date, "url": "https://saude.gov.br/", "notes": "foo"} in reports
        assert 1 == len(cases)
        self.assertDataEntry(cases, self.date, "TOTAL NO ESTADO", 12, 7)
        self.assertDataEntry(cases, self.date, "Importados/Indefinidos", 2, 2)
        self.assertDataEntry(cases, self.date, "Curitiba", 10, 5)

    def test_report_data_should_exclude_city_entries_if_spreadsheet_only_with_total(self):
        sp = baker.make(StateSpreadsheet, status=StateSpreadsheet.DEPLOYED, state=self.state, date=self.date,)
        sp_date = self.date.isoformat()
        sp.warnings = [StateSpreadsheet.ONLY_WITH_TOTAL_WARNING]
        sp.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 12,
                "date": sp_date,
                "deaths": 7,
                "place_type": "state",
                "state": self.state,
            },
            {
                "city": "Curitiba",
                "city_ibge_code": 4321,
                "confirmed": 10,
                "date": sp_date,
                "deaths": 5,
                "place_type": "city",
                "state": self.state,
            },
        ]
        sp.save()

        cases = StateSpreadsheet.objects.get_state_data("PR")["cases"]

        self.assertDataEntry(cases, self.date, "TOTAL NO ESTADO", 12, 7)
        assert 1 == len(cases[self.date])

    def test_report_data_should_list_previous_deployed_city_entries_if_spreadsheet_only_with_total(self):
        sp_date = self.date.isoformat()
        previous_deployed = baker.make(
            StateSpreadsheet, status=StateSpreadsheet.DEPLOYED, state=self.state, date=self.date,
        )
        previous_deployed.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 12,
                "date": sp_date,
                "deaths": 7,
                "place_type": "state",
                "state": self.state,
            },
            {
                "city": "Importados/Indefinidos",
                "city_ibge_code": None,
                "confirmed": 2,
                "date": sp_date,
                "deaths": 2,
                "place_type": "city",
                "state": self.state,
            },
            {
                "city": "Curitiba",
                "city_ibge_code": 4321,
                "confirmed": 10,
                "date": sp_date,
                "deaths": 5,
                "place_type": "city",
                "state": self.state,
            },
        ]
        previous_deployed.save()

        total_sp = baker.make(StateSpreadsheet, status=StateSpreadsheet.DEPLOYED, state=self.state, date=self.date,)
        total_sp_date = self.date.isoformat()
        total_sp.warnings = [StateSpreadsheet.ONLY_WITH_TOTAL_WARNING]
        total_sp.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 50,
                "date": total_sp_date,
                "deaths": 20,
                "place_type": "state",
                "state": self.state,
            },
            {
                "city": "Curitiba",
                "city_ibge_code": 4321,
                "confirmed": 8,
                "date": total_sp_date,
                "deaths": 1,
                "place_type": "city",
                "state": self.state,
            },
        ]
        total_sp.save()

        cases = StateSpreadsheet.objects.get_state_data("PR")["cases"]

        self.assertDataEntry(cases, self.date, "TOTAL NO ESTADO", 50, 20)
        self.assertDataEntry(cases, self.date, "Importados/Indefinidos", 2, 2)
        self.assertDataEntry(cases, self.date, "Curitiba", 10, 5)

    def test_report_data_should_ignore_previous_if_city_data_was_already_exported(self):
        sp_date = self.date.isoformat()
        previous_total = baker.make(
            StateSpreadsheet, status=StateSpreadsheet.DEPLOYED, state=self.state, date=self.date,
        )
        previous_total.warnings = [StateSpreadsheet.ONLY_WITH_TOTAL_WARNING]
        previous_total.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 12,
                "date": sp_date,
                "deaths": 7,
                "place_type": "state",
                "state": self.state,
            },
        ]
        previous_total.save()

        sp = baker.make(StateSpreadsheet, status=StateSpreadsheet.DEPLOYED, state=self.state, date=self.date,)
        sp_date = self.date.isoformat()
        sp.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 20,
                "date": sp_date,
                "deaths": 10,
                "place_type": "state",
                "state": self.state,
            },
            {
                "city": "Importados/Indefinidos",
                "city_ibge_code": None,
                "confirmed": 12,
                "date": sp_date,
                "deaths": 9,
                "place_type": "city",
                "state": self.state,
            },
            {
                "city": "Curitiba",
                "city_ibge_code": 4321,
                "confirmed": 8,
                "date": sp_date,
                "deaths": 1,
                "place_type": "city",
                "state": self.state,
            },
        ]
        sp.save()

        cases = StateSpreadsheet.objects.get_state_data("PR")["cases"]

        self.assertDataEntry(cases, self.date, "TOTAL NO ESTADO", 20, 10)
        self.assertDataEntry(cases, self.date, "Importados/Indefinidos", 12, 9)
        self.assertDataEntry(cases, self.date, "Curitiba", 8, 1)

    def test_ensure_previous_city_data_is_always_using_the_most_recent_one(self):
        sp_date = self.date.isoformat()
        older_previous_deployed = baker.make(
            StateSpreadsheet, status=StateSpreadsheet.DEPLOYED, state=self.state, date=self.date,
        )
        older_previous_deployed.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 12,
                "date": sp_date,
                "deaths": 7,
                "place_type": "state",
                "state": self.state,
            },
            {
                "city": "Importados/Indefinidos",
                "city_ibge_code": None,
                "confirmed": 5,
                "date": sp_date,
                "deaths": 5,
                "place_type": "city",
                "state": self.state,
            },
            {
                "city": "Curitiba",
                "city_ibge_code": 4321,
                "confirmed": 7,
                "date": sp_date,
                "deaths": 2,
                "place_type": "city",
                "state": self.state,
            },
        ]
        older_previous_deployed.save()

        previous_deployed = baker.make(
            StateSpreadsheet, status=StateSpreadsheet.DEPLOYED, state=self.state, date=self.date,
        )
        previous_deployed.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 12,
                "date": sp_date,
                "deaths": 7,
                "place_type": "state",
                "state": self.state,
            },
            {
                "city": "Importados/Indefinidos",
                "city_ibge_code": None,
                "confirmed": 2,
                "date": sp_date,
                "deaths": 2,
                "place_type": "city",
                "state": self.state,
            },
            {
                "city": "Curitiba",
                "city_ibge_code": 4321,
                "confirmed": 10,
                "date": sp_date,
                "deaths": 5,
                "place_type": "city",
                "state": self.state,
            },
        ]
        previous_deployed.save()

        total_sp = baker.make(StateSpreadsheet, status=StateSpreadsheet.DEPLOYED, state=self.state, date=self.date,)
        total_sp_date = self.date.isoformat()
        total_sp.warnings = [StateSpreadsheet.ONLY_WITH_TOTAL_WARNING]
        total_sp.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 50,
                "date": total_sp_date,
                "deaths": 20,
                "place_type": "state",
                "state": self.state,
            },
        ]
        total_sp.save()

        cases = StateSpreadsheet.objects.get_state_data("PR")["cases"]

        self.assertDataEntry(cases, self.date, "TOTAL NO ESTADO", 50, 20)
        self.assertDataEntry(cases, self.date, "Importados/Indefinidos", 2, 2)
        self.assertDataEntry(cases, self.date, "Curitiba", 10, 5)

    def test_ensure_only_first_spreadsheet_for_date_only_with_total_is_considered(self):
        sp_date = self.date.isoformat()
        older_previous_deployed = baker.make(
            StateSpreadsheet, status=StateSpreadsheet.DEPLOYED, state=self.state, date=self.date, cancelled=True,
        )
        older_previous_deployed.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 12,
                "date": sp_date,
                "deaths": 7,
                "place_type": "state",
                "state": self.state,
            },
        ]
        older_previous_deployed.warnings = [StateSpreadsheet.ONLY_WITH_TOTAL_WARNING]
        older_previous_deployed.save()

        previous_deployed = baker.make(
            StateSpreadsheet, status=StateSpreadsheet.DEPLOYED, state=self.state, date=self.date, cancelled=False
        )
        previous_deployed.table_data = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 40,
                "date": sp_date,
                "deaths": 30,
                "place_type": "state",
                "state": self.state,
            },
        ]
        previous_deployed.warnings = [StateSpreadsheet.ONLY_WITH_TOTAL_WARNING]
        previous_deployed.save()

        cases = StateSpreadsheet.objects.get_state_data("PR")["cases"]

        self.assertDataEntry(cases, self.date, "TOTAL NO ESTADO", 40, 30)
