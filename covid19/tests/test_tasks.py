import pytest
from model_bakery import baker

from django.test import TestCase

from covid19.models import StateSpreadsheet
from covid19.tasks import process_new_spreadsheet_task


class ProcessNewSpreadsheetTaskTests(TestCase):

    def test_function_is_a_task(self):
        assert getattr(process_new_spreadsheet_task, 'delay', None)

    @pytest.mark.skip("Skiped until we don't have the logic to process the spreadsheet")
    def test_do_not_process_spreadsheet_if_for_some_reason_it_is_cancelled(self):
        spreadsheet = baker.make(StateSpreadsheet, cancelled=True)
        process_new_spreadsheet_task(spreadsheet.pk)
