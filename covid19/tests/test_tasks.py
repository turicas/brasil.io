from model_bakery import baker
from unittest.mock import patch

from django.test import TestCase

from covid19.models import StateSpreadsheet
from covid19.tasks import process_new_spreadsheet_task
from covid19.spreadsheet_validator import SpreadsheetValidationErrors


class ProcessNewSpreadsheetTaskTests(TestCase):

    def test_function_is_a_task(self):
        assert getattr(process_new_spreadsheet_task, 'delay', None)

    @patch('covid19.tasks.validate_historical_data')
    def test_update_warnings_after_historical_data_validation(self, mock_validate_historical_data):
        mock_validate_historical_data.return_value = ['Warning 1', 'Warning 2']

        spreadsheet = baker.make(StateSpreadsheet)
        assert [] == spreadsheet.warnings
        spreadsheet.refresh_from_db()

        assert ['Warning 1', 'Warning 2'] == spreadsheet.warnings
        assert [] == spreadsheet.errors
        assert StateSpreadsheet.UPLOADED == spreadsheet.status

    @patch('covid19.tasks.validate_historical_data')
    def test_update_error_and_status_if_not_valid(self, mock_validate_historical_data):
        errors = ['Error 1', 'Error 2']
        exception = SpreadsheetValidationErrors()
        for e in errors:
            exception.new_error(e)
        mock_validate_historical_data.side_effect = exception

        spreadsheet = baker.make(StateSpreadsheet)
        assert [] == spreadsheet.errors
        spreadsheet.refresh_from_db()

        assert errors == spreadsheet.errors
        assert [] == spreadsheet.warnings
        assert StateSpreadsheet.CHECK_FAILED == spreadsheet.status

    @patch('covid19.tasks.validate_historical_data')
    def test_do_not_process_spreadsheet_if_for_some_reason_it_is_cancelled(self, mock_validate):
        spreadsheet = baker.make(StateSpreadsheet, cancelled=True)
        assert not mock_validate.called
