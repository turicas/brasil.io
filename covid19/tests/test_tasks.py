from django.test import TestCase

from covid19.tasks import process_new_spreadsheet_task


class ProcessNewSpreadsheetTaskTests(TestCase):

    def test_function_is_a_task(self):
        assert getattr(process_new_spreadsheet_task, 'delay', None)
