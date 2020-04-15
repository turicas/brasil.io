import pytest
import rows
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.forms import ValidationError
from django.test import TestCase

from covid19.spreadsheet_validator import format_spreadsheet_rows_as_dict


SAMPLE_SPREADSHEETS_DATA_DIR = Path(settings.BASE_DIR).joinpath('covid19', 'tests', 'data')


class FormatSpreadsheetRowsAsDictTests(TestCase):

    def setUp(self):
        sample = SAMPLE_SPREADSHEETS_DATA_DIR / 'sample-PR.csv'
        self.content = sample.read_text()

    @property
    def file_from_content(self):
        return BytesIO(str.encode(self.content))

    def test_format_valid_list_of_rows(self):
        file_rows = rows.import_from_csv(self.file_from_content)

        data = format_spreadsheet_rows_as_dict(file_rows)
        expected = {
            'total': {'confirmados': 100, 'mortes': 30},
            'importados_indefinidos': {'confirmados': 2, 'mortes': 1},
            'cidades': {
                'Abatiá': {'confirmados': 9, 'mortes': 1},
                'Adrianópolis': {'confirmados': 11, 'mortes': 2},
                'Agudos do Sul': {'confirmados': 12, 'mortes': 3},
                'Almirante Tamandaré': {'confirmados': 8, 'mortes': 4},
                'Altamira do Paraná': {'confirmados': 13, 'mortes': 5},
                'Alto Paraíso': {'confirmados': 47, 'mortes': 15},
            }
        }

        assert data == expected

    def test_alternative_columns_names_for_confirmed_cases(self):
        alternatives = ['casos confirmados', 'confirmado']
        original_content = self.content

        for alt in alternatives:
            self.content = original_content.replace('confirmados', alt)
            file_rows = rows.import_from_csv(self.file_from_content)
            data = format_spreadsheet_rows_as_dict(file_rows)

            assert data['total']['confirmados'] == 100

    def test_raise_exception_if_confirmed_cases_column_is_missing(self):
        self.content = self.content.replace('confirmados', 'xpto')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(ValidationError):
            format_spreadsheet_rows_as_dict(file_rows)

    def test_alternative_columns_names_for_deaths(self):
        alternatives = ['óbitos', 'óbito', 'obito', 'morte']
        original_content = self.content

        for alt in alternatives:
            self.content = original_content.replace('mortes', alt)
            file_rows = rows.import_from_csv(self.file_from_content)
            data = format_spreadsheet_rows_as_dict(file_rows)

            assert data['total']['mortes'] == 30

    def test_raise_exception_if_deaths_column_is_missing(self):
        self.content = self.content.replace('mortes', 'xpto')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(ValidationError):
            format_spreadsheet_rows_as_dict(file_rows)

    def test_raise_exception_if_city_column_is_missing(self):
        self.content = self.content.replace('municipio', 'xpto')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(ValidationError):
            format_spreadsheet_rows_as_dict(file_rows)

    def test_raise_exception_line_with_total_is_missing(self):
        self.content = self.content.replace('TOTAL NO ESTADO', 'TOTAL')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(ValidationError):
            format_spreadsheet_rows_as_dict(file_rows)

    def test_raise_exception_line_with_undefinitions_is_missing(self):
        self.content = self.content.replace('Importados', '')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(ValidationError):
            format_spreadsheet_rows_as_dict(file_rows)

    def test_both_confirmed_cases_and_deaths_columns_must_be_filled(self):
        original_content = self.content

        # missing confirmed cases
        self.content = original_content.replace('Abatiá,9,1', 'Abatiá,,1')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(ValidationError):
            format_spreadsheet_rows_as_dict(file_rows)

        # missing deaths
        self.content = original_content.replace('Abatiá,9,1', 'Abatiá,9,')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(ValidationError):
            format_spreadsheet_rows_as_dict(file_rows)

    def test_both_confirmed_cases_and_deaths_columns_must_be_integers(self):
        original_content = self.content

        # confirmed cases as float
        self.content = original_content.replace('Abatiá,9,1', 'Abatiá,9.10,1')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(ValidationError):
            format_spreadsheet_rows_as_dict(file_rows)

        # deaths as float
        self.content = original_content.replace('Abatiá,9,1', 'Abatiá,9,1.10')
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(ValidationError):
            format_spreadsheet_rows_as_dict(file_rows)
