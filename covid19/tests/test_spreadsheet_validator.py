from datetime import date, timedelta
from io import BytesIO
from unittest.mock import Mock, patch

import pytest
import rows
from django.conf import settings
from django.test import TestCase
from model_bakery import baker

from brazil_data.cities import get_city_info
from core.models import Table
from covid19.exceptions import SpreadsheetValidationErrors
from covid19.models import StateSpreadsheet
from covid19.spreadsheet_validator import format_spreadsheet_rows_as_dict, validate_historical_data
from covid19.tests.utils import Covid19DatasetTestCase


class FormatSpreadsheetRowsAsDictTests(TestCase):
    def setUp(self):
        sample = settings.SAMPLE_SPREADSHEETS_DATA_DIR / "sample-PR.csv"
        self.content = sample.read_text()
        self.date = date.today()
        self.uf = "PR"

    @property
    def file_from_content(self):
        return BytesIO(str.encode(self.content))

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=["warning"]))
    def test_format_valid_list_of_rows(self):
        file_rows = rows.import_from_csv(self.file_from_content)
        date = self.date.isoformat()

        data, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)
        cities_data = [
            {"nome": "Abatiá", "confirmados": 9, "mortes": 1},
            {"nome": "Adrianópolis", "confirmados": 11, "mortes": 2},
            {"nome": "Agudos do Sul", "confirmados": 12, "mortes": 3},
            {"nome": "Almirante Tamandaré", "confirmados": 8, "mortes": 4},
            {"nome": "Altamira do Paraná", "confirmados": 13, "mortes": 5},
            {"nome": "Alto Paraíso", "confirmados": 47, "mortes": 15},
        ]
        for d in cities_data:
            d["ibge"] = get_city_info(d["nome"], self.uf).city_ibge_code
        expected = [
            {
                "city": None,
                "city_ibge_code": 41,
                "confirmed": 102,
                "date": date,
                "deaths": 32,
                "place_type": "state",
                "state": "PR",
            },
            {
                "city": "Importados/Indefinidos",
                "city_ibge_code": None,
                "confirmed": 2,
                "date": date,
                "deaths": 2,
                "place_type": "city",
                "state": "PR",
            },
        ]
        expected.extend(
            [
                {
                    "city": c["nome"],
                    "city_ibge_code": c["ibge"],
                    "confirmed": c["confirmados"],
                    "date": date,
                    "deaths": c["mortes"],
                    "place_type": "city",
                    "state": "PR",
                }
                for c in cities_data
            ]
        )

        assert data == expected
        assert ["warning"] == warnings

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_alternative_columns_names_for_confirmed_cases(self):
        alternatives = ["casos confirmados", "confirmado", "confirmados"]
        original_content = self.content

        for alt in alternatives:
            self.content = original_content.replace("confirmados", alt)
            file_rows = rows.import_from_csv(self.file_from_content)
            data, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

            assert data[0]["confirmed"] == 102

    def test_raise_exception_if_confirmed_cases_column_is_missing(self):
        self.content = self.content.replace("confirmados", "xpto")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_alternative_columns_names_for_deaths(self):
        alternatives = ["óbitos", "óbito", "obito", "morte"]
        original_content = self.content

        for alt in alternatives:
            self.content = original_content.replace("mortes", alt)
            file_rows = rows.import_from_csv(self.file_from_content)
            data, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

            assert data[0]["deaths"] == 32

    def test_raise_exception_if_deaths_column_is_missing(self):
        self.content = self.content.replace("mortes", "xpto")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_alternative_columns_names_for_city(self):
        alternatives = ["município", "cidade"]
        original_content = self.content

        for alt in alternatives:
            self.content = original_content.replace("municipio", alt)
            file_rows = rows.import_from_csv(self.file_from_content)
            data, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

            assert data[0]["confirmed"] == 102

    def test_raise_exception_if_city_column_is_missing(self):
        self.content = self.content.replace("municipio", "xpto")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_raise_exception_line_with_total_is_missing(self):
        self.content = self.content.replace("TOTAL NO ESTADO", "TOTAL")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_raise_exception_line_with_undefinitions_is_missing(self):
        self.content = self.content.replace("Importados", "")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_line_can_have_none_for_all_values_if_city_has_no_cases_yet(self):
        self.content = self.content.replace("Abatiá,9,1", "Abatiá,,")
        self.content = self.content.replace("TOTAL NO ESTADO,102,32", "TOTAL NO ESTADO,93,31")
        file_rows = rows.import_from_csv(self.file_from_content)

        results, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        assert len(results) == len(file_rows) - 1
        assert "Abatiá" not in [r["city"] for r in results]

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_always_use_ibge_data_to_format_the_city_name(self):
        self.content = self.content.replace("Abatiá,9,1", "abatiá,9,1")
        file_rows = rows.import_from_csv(self.file_from_content)

        expected = {
            "city": "Abatiá",
            "city_ibge_code": get_city_info("Abatiá", "PR").city_ibge_code,
            "confirmed": 9,
            "date": self.date.isoformat(),
            "deaths": 1,
            "place_type": "city",
            "state": "PR",
        }
        results, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        assert expected in results

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_allow_zero_as_a_valid_value(self):
        original_content = self.content
        base = {
            "city": "Abatiá",
            "city_ibge_code": get_city_info("Abatiá", "PR").city_ibge_code,
            "confirmed": 9,
            "date": self.date.isoformat(),
            "deaths": 1,
            "place_type": "city",
            "state": "PR",
        }

        # zero confirmed cases
        self.content = original_content.replace("TOTAL NO ESTADO,102,32", "TOTAL NO ESTADO,93,31")
        self.content = self.content.replace("Abatiá,9,1", "Abatiá,0,0")
        expected = base.copy()
        expected["confirmed"] = 0
        expected["deaths"] = 0

        file_rows = rows.import_from_csv(self.file_from_content)
        results, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)
        assert expected in results

        # zero deaths
        self.content = original_content.replace("TOTAL NO ESTADO,102,32", "TOTAL NO ESTADO,102,31")
        self.content = self.content.replace("Abatiá,9,1", "Abatiá,9,0")
        expected = base.copy()
        expected["deaths"] = 0

        file_rows = rows.import_from_csv(self.file_from_content)
        results, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)
        assert expected in results

    def test_both_confirmed_cases_and_deaths_columns_must_be_filled(self):
        original_content = self.content

        # missing confirmed cases
        self.content = original_content.replace("Abatiá,9,1", "Abatiá,,1")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        # missing deaths
        self.content = original_content.replace("Abatiá,9,1", "Abatiá,9,")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_both_confirmed_cases_and_deaths_columns_must_be_integers(self):
        original_content = self.content

        # confirmed cases as float
        self.content = original_content.replace("Abatiá,9,1", "Abatiá,9.10,1")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        # deaths as float
        self.content = original_content.replace("Abatiá,9,1", "Abatiá,9,1.10")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_confirmed_cases_must_be_equal_or_greater_than_deaths(self):
        original_content = self.content

        self.content = original_content.replace("Abatiá,9,1", "Abatiá,9,20")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_validate_if_all_cities_exists_are_in_the_state(self):
        file_rows = rows.import_from_csv(self.file_from_content)

        with pytest.raises(SpreadsheetValidationErrors) as execinfo:
            format_spreadsheet_rows_as_dict(file_rows, self.date, "SP")

        exception = execinfo.value
        assert "Abatiá não pertence à UF SP" in exception.error_messages
        assert "Adrianópolis não pertence à UF SP" in exception.error_messages

    def test_can_not_have_negative_values(self):
        self.content = self.content.replace("Abatiá,9,1", "Abatiá,-1,-9")
        file_rows = rows.import_from_csv(self.file_from_content)

        with pytest.raises(SpreadsheetValidationErrors):
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

    def test_not_valid_if_sum_of_cases_does_not_matches_with_total(self):
        self.content = self.content.replace("TOTAL NO ESTADO,102,32", "TOTAL NO ESTADO,1000,32")
        file_rows = rows.import_from_csv(self.file_from_content)

        with pytest.raises(SpreadsheetValidationErrors) as execinfo:
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        exception = execinfo.value
        assert "A soma de casos (102) difere da entrada total (1000)." in exception.error_messages

    def test_not_valid_if_sum_of_deaths_does_not_matches_with_total(self):
        self.content = self.content.replace("TOTAL NO ESTADO,102,32", "TOTAL NO ESTADO,102,50")
        file_rows = rows.import_from_csv(self.file_from_content)

        with pytest.raises(SpreadsheetValidationErrors) as execinfo:
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        exception = execinfo.value
        assert "A soma de mortes (32) difere da entrada total (50)." in exception.error_messages

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_ignore_sum_of_cases_if_flagged(self):
        self.content = self.content.replace("TOTAL NO ESTADO,102,32", "TOTAL NO ESTADO,1000,32")
        file_rows = rows.import_from_csv(self.file_from_content)

        results, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf, skip_sum_cases=True)

        assert "A checagem da soma de casos por cidade com o valor total foi desativada." in warnings
        assert results[0]["confirmed"] == 1000

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_ignore_sum_of_deaths_if_flagged(self):
        self.content = self.content.replace("TOTAL NO ESTADO,102,32", "TOTAL NO ESTADO,102,90")
        file_rows = rows.import_from_csv(self.file_from_content)

        results, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf, skip_sum_deaths=True)

        assert "A checagem da soma de óbitos por cidade com o valor total foi desativada." in warnings
        assert results[0]["deaths"] == 90

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_do_not_check_for_totals_if_only_total_lines_data(self):
        sample = settings.SAMPLE_SPREADSHEETS_DATA_DIR / "sample-PR-no-cities-data.csv"
        assert sample.exists()
        self.content = sample.read_text()

        file_rows = rows.import_from_csv(self.file_from_content)
        data, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        assert data[0]["deaths"] == 50

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_ignore_empty_lines_when_importing(self):
        sample = settings.SAMPLE_SPREADSHEETS_DATA_DIR / "sample-PR-empty-lines.csv"
        assert sample.exists()
        self.content = sample.read_text()

        file_rows = rows.import_from_csv(self.file_from_content)
        data, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        assert len(file_rows) > 8
        assert 8 == len(data)

    def test_raise_error_if_empty_line_but_with_data(self):
        sample = settings.SAMPLE_SPREADSHEETS_DATA_DIR / "sample-PR-empty-lines.csv"
        assert sample.exists()
        self.content = sample.read_text()
        self.content = self.content.replace(",,", ",10,20")

        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors) as execinfo:
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        exception = execinfo.value
        msg = "Uma ou mais linhas com a coluna de cidade vazia possuem números de confirmados ou óbitos"
        assert msg in exception.error_messages
        assert exception.error_messages.count(msg) == 1

    @patch("covid19.spreadsheet_validator.validate_historical_data")
    def test_validate_historical_data_as_the_final_validation(self, mock_validate_historical_data):
        mock_validate_historical_data.return_value = ["warning 1", "warning 2"]

        file_rows = rows.import_from_csv(self.file_from_content)
        results, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        assert results
        assert ["warning 1", "warning 2"] == warnings
        assert 1 == mock_validate_historical_data.call_count
        on_going_spreadsheet = mock_validate_historical_data.call_args[0][0]
        assert isinstance(on_going_spreadsheet, StateSpreadsheet)
        assert on_going_spreadsheet.table_data == results
        assert on_going_spreadsheet.state == self.uf
        assert on_going_spreadsheet.date == self.date

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_undefined_can_hold_none_values_for_confirmed_and_deaths(self):
        self.content = self.content.replace("TOTAL NO ESTADO,102,32", "TOTAL NO ESTADO,100,30")
        self.content = self.content.replace("Importados/Indefinidos,2,2", "Importados/Indefinidos,,")
        file_rows = rows.import_from_csv(self.file_from_content)

        results, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        assert len(results) == len(file_rows) - 1
        assert "Importados/Indefinidos" not in [r["city"] for r in results]

    def test_validation_error_if_city_is_repeated(self):
        self.content = self.content.replace("Abatiá,9,1", "Abatiá,9,1\nAbatiá,0,0")

        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors) as execinfo:
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        exception = execinfo.value
        assert "Mais de uma entrada para Abatiá" in exception.error_messages

    def test_validation_error_if_city_formula(self):
        self.content = self.content.replace("Abatiá,9,1", "Abatiá,'=SUM(A1:A3)',1")

        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors) as execinfo:
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        exception = execinfo.value
        assert (
            'Erro no formato de algumas entradas dados: cheque para ver se a planilha não possui fórmulas ou números com ponto ou vírgula nas linhas: Abatiá"'
            in exception.error_messages
        )

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=["db warning"]))
    def test_undefined_entry_can_have_more_deaths_than_cases(self):
        self.content = self.content.replace("TOTAL NO ESTADO,102,32", "TOTAL NO ESTADO,102,33")
        self.content = self.content.replace("Importados/Indefinidos,2,2", "Importados/Indefinidos,2,3")
        file_rows = rows.import_from_csv(self.file_from_content)

        results, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        assert len(results) == len(file_rows)
        assert 2 == len(warnings)
        assert "db warning" in warnings
        assert "Importados/Indefinidos com número óbitos maior que de casos confirmados."

    @patch("covid19.spreadsheet_validator.validate_historical_data", Mock(return_value=[]))
    def test_spreadsheet_only_with_total_line_should_be_valid(self):
        self.content = "municipio,confirmados,mortes\nTOTAL NO ESTADO,102,32"
        file_rows = rows.import_from_csv(self.file_from_content)

        results, warnings = format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        assert len(results) == 1
        assert results[0]["confirmed"] == 102
        assert results[0]["deaths"] == 32

    def test_invalidate_spreadsheet_against_VALUE_error(self):
        self.content = self.content.replace("Abatiá,9,1", "Abatiá,#VALUE!,3 0")
        self.content = self.content.replace("Adrianópolis,11,2", "Adrianópolis,#VALUE!,3 0")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors) as execinfo:
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        exception = execinfo.value
        assert (
            'Erro no formato de algumas entradas dados: cheque para ver se a planilha não possui fórmulas ou números com ponto ou vírgula nas linhas: Abatiá, Adrianópolis"'
            in exception.error_messages
        )

    def test_invalidate_spreadsheet_against_float_numbers(self):
        self.content = self.content.replace("Abatiá,9,1", "Abatiá,10.000,1")
        file_rows = rows.import_from_csv(self.file_from_content)
        with pytest.raises(SpreadsheetValidationErrors) as execinfo:
            format_spreadsheet_rows_as_dict(file_rows, self.date, self.uf)

        exception = execinfo.value
        assert (
            "Erro no formato de algumas entradas dados: cheque para ver se a planilha não possui fórmulas ou números com ponto ou vírgula nas linhas: TOTAL NO ESTADO, Importados/Indefinidos, Abatiá, "  # all entries
            in exception.error_messages[0]
        )


class TestValidateSpreadsheetWithHistoricalData(Covid19DatasetTestCase):
    def setUp(self):
        self.uf = "PR"
        self.cities_cases = [
            {"city": "Abatiá", "confirmed": 9, "deaths": 1},
            {"city": "Adrianópolis", "confirmed": 11, "deaths": 2},
            {"city": "Agudos do Sul", "confirmed": 12, "deaths": 3},
            {"city": "Almirante Tamandaré", "confirmed": 8, "deaths": 4},
            {"city": "Altamira do Paraná", "confirmed": 13, "deaths": 5},
            {"city": "Alto Paraíso", "confirmed": 47, "deaths": 15},
        ]
        self.today = date.today()
        self.undefined_data = {
            "city": "Importados/Indefinidos",
            "city_ibge_code": None,
            "confirmed": 2,
            "date": self.today.isoformat(),
            "deaths": 2,
            "place_type": "city",
            "state": self.uf,
        }
        self.total_data = {
            "city": None,
            "city_ibge_code": 41,
            "confirmed": 102,
            "date": self.today.isoformat(),
            "deaths": 32,
            "place_type": "state",
            "state": self.uf,
        }
        self.cities_data = [
            {
                "city": c["city"],
                "city_ibge_code": get_city_info(c["city"], self.uf).city_ibge_code,
                "confirmed": c["confirmed"],
                "date": self.today.isoformat(),
                "deaths": c["deaths"],
                "place_type": "city",
                "state": self.uf,
            }
            for c in self.cities_cases
        ]
        self.spreadsheet = baker.prepare(StateSpreadsheet, state=self.uf, date=self.today)

    def new_spreadsheet_with_data(self, table_data, **kwargs):
        sp = baker.make(StateSpreadsheet, **kwargs)

        table_data = [d.copy() for d in table_data]
        for t in table_data:
            t["date"] = sp.date.isoformat()
        sp.table_data = table_data
        sp.save()

        return sp

    def test_can_create_covid_19_cases_entries(self):
        table = Table.objects.for_dataset("covid19").named("caso")
        assert table == self.table
        Covid19Cases = self.TableModel

        assert 0 == len(Covid19Cases.objects.all())
        cases_entry = baker.make(Covid19Cases, _fill_optional=["city"])
        assert 1 == len(Covid19Cases.objects.all())

        cases_entry.refresh_from_db()
        assert cases_entry.date
        assert cases_entry.state
        assert cases_entry.city

    def test_raise_validation_error_previous_city_not_present_in_data(self):
        self.spreadsheet.table_data = [self.total_data, self.undefined_data]  # no cities
        self.new_spreadsheet_with_data(
            date=self.today - timedelta(days=2),
            state=self.uf,
            status=StateSpreadsheet.DEPLOYED,
            table_data=[self.total_data, self.undefined_data] + self.cities_data,
        )

        # older city from the same state is not considered
        self.new_spreadsheet_with_data(
            date=self.today - timedelta(days=8),
            state=self.uf,
            status=StateSpreadsheet.DEPLOYED,
            table_data=[{"place_type": "city", "confirmed": 1000, "deaths": 1000, "city": "bar",}],
        )

        # report with date greater than the spreadsheet's one shouldn't be considered
        self.new_spreadsheet_with_data(
            date=self.today + timedelta(days=8),
            state=self.uf,
            status=StateSpreadsheet.DEPLOYED,
            table_data=[{"place_type": "city", "confirmed": 500, "deaths": 500, "city": "bar",}],
        )

        with pytest.raises(SpreadsheetValidationErrors) as execinfo:
            validate_historical_data(self.spreadsheet)

        exception = execinfo.value
        assert len(self.cities_cases) == len(exception.error_messages)
        for city_name in [c["city"] for c in self.cities_cases]:
            msg = f"{city_name} possui dados históricos e não está presente na planilha."
            assert msg in exception.error_messages

    def test_is_valid_if_historical_data_has_the_same_values_as_the_new_import(self):
        self.spreadsheet.table_data = [self.total_data, self.undefined_data] + self.cities_data
        self.new_spreadsheet_with_data(
            date=self.today - timedelta(days=2),
            state=self.uf,
            status=StateSpreadsheet.DEPLOYED,
            table_data=[self.total_data, self.undefined_data] + self.cities_data,
        )

        warnings = validate_historical_data(self.spreadsheet)

        assert not warnings

    def test_return_warning_message_if_number_of_cases_is_lower_than_previous_day(self):
        self.spreadsheet.table_data = [self.total_data, self.undefined_data] + self.cities_data
        table_data = [self.total_data, self.undefined_data]
        for cases_data in [c.copy() for c in self.cities_data]:
            cases_data["confirmed"] = 200
            table_data.append(cases_data)
        self.new_spreadsheet_with_data(
            date=self.today - timedelta(days=2), state=self.uf, status=StateSpreadsheet.DEPLOYED, table_data=table_data
        )

        warnings = validate_historical_data(self.spreadsheet)

        assert len(self.cities_cases) == len(warnings)
        for city_name in [c["city"] for c in self.cities_cases]:
            msg = f"Números de confirmados ou óbitos em {city_name} é menor que o anterior."
            assert msg in warnings

    def test_return_warning_message_if_number_of_deaths_is_lower_than_previous_day(self):
        self.spreadsheet.table_data = [self.total_data, self.undefined_data] + self.cities_data
        table_data = [self.total_data, self.undefined_data]
        for cases_data in [c.copy() for c in self.cities_data]:
            cases_data["deaths"] = 200
            table_data.append(cases_data)
        self.new_spreadsheet_with_data(
            date=self.today - timedelta(days=2), state=self.uf, status=StateSpreadsheet.DEPLOYED, table_data=table_data
        )

        warnings = validate_historical_data(self.spreadsheet)

        assert len(self.cities_cases) == len(warnings)
        for city_name in [c["city"] for c in self.cities_cases]:
            msg = f"Números de confirmados ou óbitos em {city_name} é menor que o anterior."
            assert msg in warnings

    def test_guarantee_warnings_for_new_lower_total_and_undefined_numbers(self):
        self.spreadsheet.table_data = [self.total_data.copy(), self.undefined_data.copy()]
        table_data = []
        for cases_data in [c.copy() for c in [self.total_data, self.undefined_data]]:
            cases_data["deaths"] = 200
            table_data.append(cases_data)
        self.new_spreadsheet_with_data(
            date=self.today - timedelta(days=2), state=self.uf, status=StateSpreadsheet.DEPLOYED, table_data=table_data,
        )

        undefined_name = self.undefined_data["city"]
        expected = [
            f"Números de confirmados ou óbitos em {undefined_name} é menor que o anterior.",
            "Números de confirmados ou óbitos totais é menor que o total anterior.",
        ]
        warnings = validate_historical_data(self.spreadsheet)
        self.spreadsheet.warnings = warnings

        assert expected == warnings
        assert self.spreadsheet.only_with_total_entry is False

    def test_if_city_is_not_present_and_previous_report_has_0_for_both_counters_add_the_entry(self):
        city_data = self.cities_data.pop(0)
        city_data["deaths"] = 0
        city_data["confirmed"] = 0
        table_data = [self.total_data, self.undefined_data, city_data]
        self.new_spreadsheet_with_data(
            date=self.today - timedelta(days=2), state=self.uf, status=StateSpreadsheet.DEPLOYED, table_data=table_data,
        )
        self.spreadsheet.table_data = [self.total_data, self.undefined_data] + self.cities_data

        expected = city_data.copy()
        expected["date"] = self.today.isoformat()
        assert expected not in self.spreadsheet.table_data

        warnings = validate_historical_data(self.spreadsheet)

        assert [
            f"{city_data['city']} possui dados históricos zerados/nulos, não presente na planilha e foi adicionado."
        ] == warnings
        assert expected in self.spreadsheet.table_data

    def test_reuse_past_data_if_city_not_present_in_data_with_only_total_sum(self):
        table_data = self.cities_data + [self.total_data, self.undefined_data]
        recent = self.new_spreadsheet_with_data(
            date=self.today - timedelta(days=2), state=self.uf, status=StateSpreadsheet.DEPLOYED, table_data=table_data,
        )

        self.total_data["deaths"] = 2
        self.total_data["confirmed"] = 5
        self.spreadsheet.table_data = [self.total_data]  # only total

        warnings = validate_historical_data(self.spreadsheet)
        self.spreadsheet.warnings = warnings

        assert self.total_data in self.spreadsheet.table_data
        assert self.undefined_data in self.spreadsheet.table_data
        for city_data in self.cities_data:
            assert city_data in self.spreadsheet.table_data

        assert 2 == len(warnings)
        assert (
            f"Planilha importada somente com dados totais. Dados de cidades foram reutilizados da importação do dia {recent.date.isoformat()}."
            in warnings
        )
        assert "Números de confirmados ou óbitos totais é menor que o total anterior." in warnings
        assert self.spreadsheet.get_total_data()["deaths"] == 2
        assert self.spreadsheet.get_total_data()["confirmed"] == 5
        assert self.spreadsheet.only_with_total_entry is True

    def test_accept_first_spreadsheet_only_with_total_tada(self):
        self.spreadsheet.table_data = [self.total_data]  # only total

        warnings = validate_historical_data(self.spreadsheet)
        self.spreadsheet.warnings = warnings

        assert 1 == len(self.spreadsheet.table_data)
        assert self.total_data in self.spreadsheet.table_data
        assert ["Planilha importada somente com dados totais."] == warnings
        assert self.spreadsheet.only_with_total_entry is True

    def assert_case_data_from_db(self, state, date, compare_data):
        # From a given state and date, checks if `compare_data` is equal to
        # what is returned by StateSpreadsheet.objects.get_state_data

        def replace_city_name(name):
            if name is None:
                return "TOTAL NO ESTADO"
            else:
                return name

        db_data = StateSpreadsheet.objects.get_state_data(state)
        db_cases = db_data["cases"][date]
        sp_data = {
            replace_city_name(case["city"]): {"confirmed": case["confirmed"], "deaths": case["deaths"],}
            for case in compare_data
            if case["date"] == str(date)
        }
        assert db_cases == sp_data

    def test_deployed_cancelled_spreadsheets_should_be_used_if_no_active_is_deployed(self):
        # First, create a deployed spreadsheet for 2 days ago
        StateSpreadsheet.objects.filter(state=self.uf).delete()
        date = self.today
        data_1 = [self.total_data, self.undefined_data] + self.cities_data
        data_2 = []
        for case in data_1:
            case = case.copy()
            case["deaths"] = 9999
            case["confirmed"] = 9999
            data_2.append(case)

        self.new_spreadsheet_with_data(
            date=date, state=self.uf, status=StateSpreadsheet.DEPLOYED, cancelled=True, table_data=[self.total_data],
        )
        sp2 = self.new_spreadsheet_with_data(
            date=date, state=self.uf, status=StateSpreadsheet.DEPLOYED, cancelled=True, table_data=data_1,
        )
        sp3 = self.new_spreadsheet_with_data(
            date=date, state=self.uf, status=StateSpreadsheet.DEPLOYED, cancelled=False, table_data=data_2,
        )

        # Data for this state/date should be the same as sp3
        self.assert_case_data_from_db(self.uf, date, sp3.table_data)

        # Changind sp3 to CHECK_FAILED: data for this state/date should be the
        # same as sp2
        sp3.status = StateSpreadsheet.CHECK_FAILED
        sp3.save()
        self.assert_case_data_from_db(self.uf, date, sp2.table_data)
