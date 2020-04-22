import io
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from covid19.exceptions import SpreadsheetValidationErrors


class ImportSpreadsheetProxyViewTests(TestCase):

    def setUp(self):
        self.url = reverse('covid19:spreadsheet_proxy', args=['RJ'])

    @patch('covid19.views.create_merged_state_spreadsheet', autospec=True)
    def test_return_spreadsheet_for_state(self, mock_merge):
        mock_merge.return_value = io.BytesIO(b'content')

        response = self.client.get(self.url)

        assert 200 == response.status_code
        assert b'content' == response.content
        mock_merge.assert_called_once_with('RJ')

    def test_404_if_invalid_state(self):
        self.url = reverse('covid19:spreadsheet_proxy', args=['XX'])
        response = self.client.get(self.url)
        assert 404 == response.status_code

    @patch('covid19.views.create_merged_state_spreadsheet', autospec=True)
    def test_400_if_spreadsheet_validation_error(self, mock_merge):
        exception = SpreadsheetValidationErrors()
        exception.new_error('error 1')
        exception.new_error('error 2')
        mock_merge.side_effect =  exception

        self.url = reverse('covid19:spreadsheet_proxy', args=['RJ'])
        response = self.client.get(self.url)

        assert 400 == response.status_code
        assert {'errors': ['error 1', 'error 2']} == response.json()
