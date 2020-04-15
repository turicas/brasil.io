from django_rq import job

from covid19.models import StateSpreadsheet
from covid19.spreadsheet_validator import validate_historical_data, SpreadsheetValidationErrors


@job
def process_new_spreadsheet_task(spreadsheet_pk):
    try:
        spreadsheet = StateSpreadsheet.objects.filter_active().get(pk=spreadsheet_pk)
    except StateSpreadsheet.DoesNotExist:
        return None

    try:
        spreadsheet.warnings = validate_historical_data(spreadsheet)
        spreadsheet.save()
    except SpreadsheetValidationErrors as exception:
        spreadsheet.errors = exception.error_messages
        spreadsheet.save()

    # TODO https://github.com/turicas/brasil.io/issues/212
