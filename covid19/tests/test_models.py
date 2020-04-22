import pytest
import shutil
from copy import deepcopy
from datetime import date, timedelta
from model_bakery import baker
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

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
                "state": 'PR',
            },
            {
                "city": "Importados/Indefinidos",
                "city_ibge_code": None,
                "confirmed": 2,
                "date": data,
                "deaths": 2,
                "place_type": "city",
                "state": 'PR',
            },
            {
                "city": 'Curitiba',
                "city_ibge_code": 4321,
                "confirmed": 10,
                "date": data,
                "deaths": 5,
                "place_type": "city",
                "state": 'PR',
            }
        ]

    def tearDown(self):
        if Path(settings.MEDIA_ROOT).exists():
            shutil.rmtree(settings.MEDIA_ROOT)

    def test_format_filename_to_add_uf_date_username(self):
        today = date.today()

        spreadsheet = baker.make(
            StateSpreadsheet,
            user__username='foo',
            state='rj',
            date=today,
            _create_files=True,  # will create a dummy .txt file
        )
        expected = f'{settings.MEDIA_ROOT}/covid19/RJ/casos-RJ-{today.isoformat()}-foo-1.txt'

        assert expected == spreadsheet.file.path

    def test_format_filename_counting_previous_uploads_from_user(self):
        today = date.today()
        user = baker.make(settings.AUTH_USER_MODEL, username='foo')
        state = 'rj'
        prev_qtd = 4
        baker.make(
            StateSpreadsheet,
            user=user,
            state=state,
            date=today,
            _quantity=prev_qtd
        )
        baker.make(  # other state, same date
            StateSpreadsheet,
            user=user,
            state='sp',
            date=today,
        )
        baker.make(  # other date, same state
            StateSpreadsheet,
            user=user,
            state=state,
            date=today + timedelta(days=1),
        )
        baker.make(  # same date, same state, other user
            StateSpreadsheet,
            user__username='new_user',
            state=state,
            date=today,
        )

        spreadsheet = baker.make(
            StateSpreadsheet,
            user=user,
            state=state,
            date=today,
            _create_files=True
        )
        expected = f'{settings.MEDIA_ROOT}/covid19/RJ/casos-RJ-{today.isoformat()}-foo-5.txt'

        assert expected == spreadsheet.file.path

    def test_filter_older_versions_exclude_the_object_if_id(self):
        kwargs = {
            'date': date.today(), 'user': baker.make(settings.AUTH_USER_MODEL), 'state': 'rj',
        }
        baker.make(StateSpreadsheet, _quantity=3, **kwargs)

        spreadsheet = baker.prepare(StateSpreadsheet, **kwargs)
        assert 3 == StateSpreadsheet.objects.filter_older_versions(spreadsheet).count()

        spreadsheet.save()
        spreadsheet.refresh_from_db()
        assert 3 == StateSpreadsheet.objects.filter_older_versions(spreadsheet).count()

    @patch('covid19.signals.process_new_spreadsheet_task', autospec=True)
    def test_cancel_previous_imports_from_user_for_same_state_and_data(
        self, mocked_process_new_spreadsheet
    ):
        kwargs = {
            'date': date.today(), 'user': baker.make(settings.AUTH_USER_MODEL), 'state': 'RJ',
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
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state='PR', _quantity=2)
        sp1.table_data = deepcopy(self.table_data)
        sp2.table_data = deepcopy(self.table_data)

        assert [] == sp1.compare_to_spreadsheet(sp2)

    def test_compare_error_if_not_from_same_state(self):
        sp1 = baker.make(StateSpreadsheet, date=date.today(), state='RJ')
        sp2 = baker.make(StateSpreadsheet, date=date.today(), state='PR')

        sp1.table_data = deepcopy(self.table_data)
        sp2.table_data = deepcopy(self.table_data)

        assert ["Estados das planilhas são diferentes."] == sp1.compare_to_spreadsheet(sp2)

    def test_compare_error_if_not_from_date(self):
        yesterday = date.today() - timedelta(days=1)
        sp1 = baker.make(StateSpreadsheet, date=yesterday, state='PR')
        sp2 = baker.make(StateSpreadsheet, date=date.today(), state='PR')

        sp1.table_data = deepcopy(self.table_data)
        sp2.table_data = deepcopy(self.table_data)

        assert ["Datas das planilhas são diferentes."] == sp1.compare_to_spreadsheet(sp2)

    def test_error_if_mismatch_of_total_numbers(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state='PR', _quantity=2)
        sp1.table_data = deepcopy(self.table_data)

        self.table_data[0]['deaths'] = 0
        sp2.table_data = self.table_data
        expected = ["Número de casos confirmados ou óbitos diferem para Total."]

        assert expected == sp1.compare_to_spreadsheet(sp2)

    def test_error_if_mismatch_of_city_numbers(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state='PR', _quantity=2)
        sp1.table_data = deepcopy(self.table_data)

        self.table_data[1]['deaths'] = 0
        self.table_data[2]['confirmed'] = 0
        sp2.table_data = self.table_data
        expected = [
            "Número de casos confirmados ou óbitos diferem para Importados/Indefinidos.",
            "Número de casos confirmados ou óbitos diferem para Curitiba.",
        ]

        assert sorted(expected) == sorted(sp1.compare_to_spreadsheet(sp2))

    def test_error_if_mismatch_because_other_cities_does_not_exist(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state='PR', _quantity=2)

        sp1.table_data = self.table_data
        expected = [
            "Número de casos confirmados ou óbitos diferem para Total.",
            "Importados/Indefinidos está na planilha (aqui) mas não na outra usada para a comparação (lá).",
            "Curitiba está na planilha (aqui) mas não na outra usada para a comparação (lá).",
        ]

        assert sorted(expected) == sorted(sp1.compare_to_spreadsheet(sp2))

    def test_error_if_mismatch_because_other_cities_exists_only_in_the_other_spreadsheet(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state='PR', _quantity=2)

        sp1.table_data = self.table_data[:-1]
        sp2.table_data = self.table_data
        expected = [
            "Curitiba está na planilha usada para a comparação (lá) mas não na importada (aqui).",
        ]

        assert sorted(expected) == sorted(sp1.compare_to_spreadsheet(sp2))

    def test_link_to_matching_spreadsheet_peer_for_valid_spreadsheet(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state='PR', _quantity=2)
        sp1.table_data = deepcopy(self.table_data)
        sp1.save()
        sp2.table_data = deepcopy(self.table_data)
        sp2.save()

        assert (True, []) == sp1.link_to_matching_spreadsheet_peer()
        sp1.refresh_from_db()
        sp2.refresh_from_db()
        assert sp2 == sp1.peer_review
        assert sp1 == sp2.peer_review


    def test_raise_exception_if_single_spreadsheet(self):
        sp1 = baker.make(StateSpreadsheet, date=date.today(), state='RJ')
        sp2 = baker.make(StateSpreadsheet, date=date.today(), state='PR')

        with pytest.raises(OnlyOneSpreadsheetException):
            sp1.link_to_matching_spreadsheet_peer()

    def test_link_to_matching_spreadsheet_peer_for_not_matching_spreadsheets(self):
        sp1, sp2 = baker.make(StateSpreadsheet, date=date.today(), state='PR', _quantity=2)
        sp1.table_data = deepcopy(self.table_data)
        sp1.save()

        self.table_data[0]['deaths'] = 0
        sp2.table_data = self.table_data
        sp2.save()
        expected = ["Número de casos confirmados ou óbitos diferem para Total."]

        assert (False, expected) == sp1.link_to_matching_spreadsheet_peer()

    def test_import_to_final_dataset_update_spreadsheet_status(self):
        spreadsheet = baker.make(StateSpreadsheet)
        assert StateSpreadsheet.UPLOADED == spreadsheet.status
        assert not StateSpreadsheet.objects.deployed().exists()

        spreadsheet.import_to_final_dataset()
        spreadsheet.refresh_from_db()

        assert StateSpreadsheet.DEPLOYED == spreadsheet.status
        assert spreadsheet in StateSpreadsheet.objects.deployed()
