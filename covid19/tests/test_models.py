import shutil
from datetime import date, timedelta
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
        expected = f'{settings.MEDIA_ROOT}/rj/casos-rj-{today.isoformat()}-foo-5.txt'

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
        expected = f'{settings.MEDIA_ROOT}/rj/casos-rj-{today.isoformat()}-foo-5.txt'

        assert expected == spreadsheet.file.path
