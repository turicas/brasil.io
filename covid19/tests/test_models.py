import shutil
from datetime import date
from model_bakery import baker

from django.conf import settings
from django.test import TestCase

from covid19.models import StateSpreadsheet


class StateSpreadsheetTests(TestCase):

    def tearDown(self):
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
        expected = f'{settings.MEDIA_ROOT}/rj/casos-rj-{today.isoformat()}-foo-1.txt'

        assert expected == spreadsheet.file.path
