import rows
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from covid19.spreadsheet_validator import format_spreadsheet_rows_as_dict


SAMPLE_SPREADSHEETS_DATA_DIR = Path(settings.BASE_DIR).joinpath('covid19', 'tests', 'data')


class FormatSpreadsheetRowsAsDict(TestCase):

    def test_format_valid_list_of_rows(self):
        valid_csv = SAMPLE_SPREADSHEETS_DATA_DIR / 'sample-PR.csv'
        file_rows = rows.import_from_csv(valid_csv)

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
