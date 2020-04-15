import pytest
import rows
from datetime import date
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from brazil_data.cities import get_city_info
from covid19.spreadsheet_validator import format_spreadsheet_rows_as_dict, SpreadsheetValidationErrors


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
                "city": "TOTAL NO ESTADO",
                "city_ibge_code": 41,
                "confirmed": 100,
                "date": date,
                "deaths": 30,
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

            assert data[0]['confirmed'] == 100

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

            assert data[0]['deaths'] == 30

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

            assert data[0]['confirmed'] == 100

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
