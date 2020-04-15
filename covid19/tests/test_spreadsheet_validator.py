import pytest
import rows
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from model_bakery import baker

from django.conf import settings
from django.test import TestCase

from brazil_data.cities import get_city_info
from core.models import Table
from covid19.models import StateSpreadsheet
from covid19.spreadsheet_validator import (
    format_spreadsheet_rows_as_dict,
    SpreadsheetValidationErrors,
    validate_historical_data
)
from covid19.tests.utils import Covid19DatasetTestCase


SAMPLE_SPREADSHEETS_DATA_DIR = Path(settings.BASE_DIR).joinpath('covid19', 'tests', 'data')


class FormatSpreadsheetRowsAsDictTests(TestCase):

    def setUp(self):
        sample = SAMPLE_SPREADSHEETS_DATA_DIR / 'sample-PR.csv'
        self.content = sample.read_text()
        self.date = date.today()
        self.uf = 'PR'

    @property
    def file_from_content(self):
        return BytesIO(str.encode(self.content))

    def test_format_valid_list_of_rows(self):
        file_rows = rows.import_from_csv(self.file_from_content)
        date = self.date.isoformat()

        data = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)
        cities_data = [
            {'nome': 'Abatiá', 'confirmados': 9, 'mortes': 1},
            {'nome': 'Adrianópolis', 'confirmados': 11, 'mortes': 2},
            {'nome': 'Agudos do Sul', 'confirmados': 12, 'mortes': 3},
            {'nome': 'Almirante Tamandaré', 'confirmados': 8, 'mortes': 4},
            {'nome': 'Altamira do Paraná', 'confirmados': 13, 'mortes': 5},
            {'nome': 'Alto Paraíso', 'confirmados': 47, 'mortes': 15},
        ]
        for d in cities_data:
            d['ibge'] = get_city_info(d['nome'], self.uf).city_ibge_code
        expected = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 102,
                "date": date,
                "deaths": 32,
                "place_type": "state",
                "state": 'PR',
            },
            {
                "city": "Importados/Indefinidos",
                "city_ibge_code": None,
                "confirmed": 2,
                "date": date,
                "deaths": 2,
                "place_type": "city",
                "state": 'PR',
            },
        ]
        expected.extend([
            {
                "city": c['nome'],
                "city_ibge_code": c['ibge'],
                "confirmed": c['confirmados'],
                "date": date,
                "deaths": c['mortes'],
                "place_type": "city",
                "state": 'PR',
            }
            for c in cities_data
        ])

        assert data == expected

    def test_alternative_columns_names_for_confirmed_cases(self):
        alternatives = ['casos confirmados', 'confirmado', 'confirmados']
        original_content = self.content

        for alt in alternatives:
            self.content = original_content.replace('confirmados', alt)
            file_rows = rows.import_from_csv(self.file_from_content)
            data = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

            assert data[0]['confirmed'] == 102

    def test_raise_exception_if_confirmed_cases_column_is_missing(self):
        self.content = self.content.replace('confirmados', 'xpto')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_alternative_columns_names_for_deaths(self):
        alternatives = ['óbitos', 'óbito', 'obito', 'morte']
        original_content = self.content

        for alt in alternatives:
            self.content = original_content.replace('mortes', alt)
            file_rows = rows.import_from_csv(self.file_from_content)
            data = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

            assert data[0]['deaths'] == 32

    def test_raise_exception_if_deaths_column_is_missing(self):
        self.content = self.content.replace('mortes', 'xpto')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_alternative_columns_names_for_city(self):
        alternatives = ['município', 'cidade']
        original_content = self.content

        for alt in alternatives:
            self.content = original_content.replace('municipio', alt)
            file_rows = rows.import_from_csv(self.file_from_content)
            data = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

            assert data[0]['confirmed'] == 102

    def test_raise_exception_if_city_column_is_missing(self):
        self.content = self.content.replace('municipio', 'xpto')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_raise_exception_line_with_total_is_missing(self):
        self.content = self.content.replace('TOTAL NO ESTADO', 'TOTAL')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_raise_exception_line_with_undefinitions_is_missing(self):
        self.content = self.content.replace('Importados', '')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_line_can_have_none_for_all_values_if_city_has_no_cases_yet(self):
        self.content = self.content.replace('Abatiá,9,1', 'Abatiá,,')
        self.content = self.content.replace('TOTAL NO ESTADO,102,32', 'TOTAL NO ESTADO,93,31')
        file_rows = rows.import_from_csv(self.file_from_content)

        expected = {
            "city": 'Abatiá',
            "city_ibge_code": get_city_info('Abatiá', 'PR').city_ibge_code,
            "confirmed": 0,
            "date": self.date.isoformat(),
            "deaths": 0,
            "place_type": "city",
            "state": 'PR',
        }
        results = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        assert expected in results

    def test_always_use_ibge_data_to_format_the_city_name(self):
        self.content = self.content.replace('Abatiá,9,1', 'abatiá,9,1')
        file_rows = rows.import_from_csv(self.file_from_content)

        expected = {
            "city": 'Abatiá',
            "city_ibge_code": get_city_info('Abatiá', 'PR').city_ibge_code,
            "confirmed": 9,
            "date": self.date.isoformat(),
            "deaths": 1,
            "place_type": "city",
            "state": 'PR',
        }
        results = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        assert expected in results

    def test_both_confirmed_cases_and_deaths_columns_must_be_filled(self):
        original_content = self.content

        # missing confirmed cases
        self.content = original_content.replace('Abatiá,9,1', 'Abatiá,,1')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        # missing deaths
        self.content = original_content.replace('Abatiá,9,1', 'Abatiá,9,')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_both_confirmed_cases_and_deaths_columns_must_be_integers(self):
        original_content = self.content

        # confirmed cases as float
        self.content = original_content.replace('Abatiá,9,1', 'Abatiá,9.10,1')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        # deaths as float
        self.content = original_content.replace('Abatiá,9,1', 'Abatiá,9,1.10')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_confirmed_cases_must_be_equal_or_greater_than_deaths(self):
        original_content = self.content

        self.content = original_content.replace('Abatiá,9,1', 'Abatiá,9,20')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_validate_if_all_cities_exists_are_in_the_state(self):
        file_rows = rows.import_from_csv(self.file_from_content)

        with pytest.raises(SpreadsheetValidationErrors) as execinfo:
            format_spreadsheet_rows_as_dict(file_rows, self.date, 'SP')

        exception = execinfo.value
        assert "Abatiá não pertence à UF SP" in exception.error_messages
        assert "Adrianópolis não pertence à UF SP" in exception.error_messages

    def test_can_not_have_negative_values(self):
        self.content = self.content.replace('Abatiá,9,1', 'Abatiá,-1,-9')
        file_rows = rows.import_from_csv(self.file_from_content)

        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_not_valid_if_sum_of_cases_does_not_matches_with_total(self):
        self.content = self.content.replace('TOTAL NO ESTADO,102,32', 'TOTAL NO ESTADO,1000,32')
        file_rows = rows.import_from_csv(self.file_from_content)

        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_not_valid_if_sum_of_deaths_does_not_matches_with_total(self):
        self.content = self.content.replace('TOTAL NO ESTADO,102,32', 'TOTAL NO ESTADO,102,50')
        file_rows = rows.import_from_csv(self.file_from_content)

        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_do_not_check_for_totals_if_only_total_lines_data(self):
        sample = SAMPLE_SPREADSHEETS_DATA_DIR / 'sample-PR-no-cities-data.csv'
        assert sample.exists()
        self.content = sample.read_text()

        file_rows = rows.import_from_csv(self.file_from_content)
        data = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        assert data[0]['deaths'] == 50


class TestValidateSpreadsheetWithHistoricalData(Covid19DatasetTestCase):

    def setUp(self):
        self.uf = 'PR'
        self.cities_cases = [
            {'state': 'PR', 'city': 'Abatiá', 'confirmed': 9, 'deaths': 1},
            {'state': 'PR', 'city': 'Adrianópolis', 'confirmed': 11, 'deaths': 2},
            {'state': 'PR', 'city': 'Agudos do Sul', 'confirmed': 12, 'deaths': 3},
            {'state': 'PR', 'city': 'Almirante Tamandaré', 'confirmed': 8, 'deaths': 4},
            {'state': 'PR', 'city': 'Altamira do Paraná', 'confirmed': 13, 'deaths': 5},
            {'state': 'PR', 'city': 'Alto Paraíso', 'confirmed': 47, 'deaths': 15},
        ]
        self.today = date.today()
        self.undefined_data = {
            "city": "Importados/Indefinidos",
            "city_ibge_code": None,
            "confirmed": 2,
            "date": self.today.isoformat(),
            "deaths": 2,
            "place_type": "city",
            "state": 'PR',
        }
        self.total_data = {
            "city": None,
            "city_ibge_code": 41,
            "confirmed": 102,
            "date": self.today.isoformat(),
            "deaths": 32,
            "place_type": "state",
            "state": 'PR',
        }
        self.cities_data = [
            {
                "city": c['city'],
                "city_ibge_code": get_city_info(c['city'], self.uf).city_ibge_code,
                "confirmed": c['confirmed'],
                "date": self.today.isoformat(),
                "deaths": c['deaths'],
                "place_type": "city",
                "state": c['state'],
            }
            for c in self.cities_cases
        ]
        self._spreadsheet = None

    # this has to be a property due to conflicts between setUp and setUpTestData
    @property
    def spreadsheet(self):
        if not self._spreadsheet:
            self._spreadsheet = baker.make(StateSpreadsheet, state='PR', date=self.today)
        return self._spreadsheet

    def test_can_create_covid_19_cases_entries(self):
        table = Table.objects.for_dataset('covid19').named('caso')
        assert table == self.cases_table
        Covid19Cases = self.Covid19Cases

        assert 0 == len(Covid19Cases.objects.all())
        cases_entry = baker.make(Covid19Cases, _fill_optional=['city'])
        assert 1 == len(Covid19Cases.objects.all())

        cases_entry.refresh_from_db()
        assert cases_entry.date
        assert cases_entry.state
        assert cases_entry.city

    def test_raise_validation_error_previous_city_not_present_in_data(self):
        Covid19Cases = self.Covid19Cases
        self.spreadsheet.table_data = [self.total_data, self.undefined_data]  # no cities
        for cases_data in [c.copy() for c in self.cities_data]:
            cases_data['date'] = self.today - timedelta(days=2)
            baker.make(Covid19Cases, **cases_data)

        # older city from the same state is not considered
        baker.make(Covid19Cases, date=self.today - timedelta(days=8), state='RR', place_type='city')

        # a more recent report, but from other state
        baker.make(Covid19Cases, date=self.today, state='RR', place_type='city')

        with pytest.raises(SpreadsheetValidationErrors) as execinfo:
            validate_historical_data(self.spreadsheet)

        exception = execinfo.value
        assert len(self.cities_cases) == len(exception.error_messages)
        for city_name in [c['city'] for c in self.cities_cases]:
            msg = f"{city_name} possui dados históricos e não está presente na planilha"
            assert msg in exception.error_messages

    def test_is_valid_if_historical_data_has_the_same_values_as_the_new_import(self):
        Covid19Cases = self.Covid19Cases
        self.spreadsheet.table_data = [self.total_data, self.undefined_data] + self.cities_data
        for cases_data in [c.copy() for c in self.cities_data]:
            cases_data['date'] = self.today - timedelta(days=1)
            baker.make(Covid19Cases, **cases_data)

        warnings = validate_historical_data(self.spreadsheet)

        assert not warnings

    def test_return_warning_message_if_number_of_cases_is_lower_than_previous_day(self):
        Covid19Cases = self.Covid19Cases
        self.spreadsheet.table_data = [self.total_data, self.undefined_data] + self.cities_data
        for cases_data in [c.copy() for c in self.cities_data]:
            cases_data['date'] = self.today - timedelta(days=1)
            baker.make(Covid19Cases, **cases_data)

        Covid19Cases.objects.all().update(confirmed=200)

        warnings = validate_historical_data(self.spreadsheet)

        assert len(self.cities_cases) == len(warnings)
        for city_name in [c['city'] for c in self.cities_cases]:
            msg = f"Números de confirmados ou óbitos em {city_name} é menor que o anterior."
            assert msg in warnings

    def test_return_warning_message_if_number_of_deaths_is_lower_than_previous_day(self):
        Covid19Cases = self.Covid19Cases
        self.spreadsheet.table_data = [self.total_data, self.undefined_data] + self.cities_data
        for cases_data in [c.copy() for c in self.cities_data]:
            cases_data['date'] = self.today - timedelta(days=1)
            baker.make(Covid19Cases, **cases_data)

        Covid19Cases.objects.all().update(deaths=200)

        warnings = validate_historical_data(self.spreadsheet)

        assert len(self.cities_cases) == len(warnings)
        for city_name in [c['city'] for c in self.cities_cases]:
            msg = f"Números de confirmados ou óbitos em {city_name} é menor que o anterior."
            assert msg in warnings

    def test_make_sure_previous_total_and_undefined_entries_are_ignored(self):
        Covid19Cases = self.Covid19Cases
        self.spreadsheet.table_data = [self.total_data.copy(), self.undefined_data.copy()]
        self.total_data['date'] = self.today - timedelta(days=1)
        baker.make(Covid19Cases, **self.total_data)
        self.undefined_data['date'] = self.today - timedelta(days=1)
        baker.make(Covid19Cases, **self.undefined_data)

        Covid19Cases.objects.all().update(deaths=200)
        warnings = validate_historical_data(self.spreadsheet)

        assert [] == warnings
