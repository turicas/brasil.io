from django_rq import job

from covid19.exceptions import OnlyOneSpreadsheetException
from covid19.models import StateSpreadsheet
from covid19.notifications import notify_new_spreadsheet, notify_spreadsheet_mismatch


@job
def process_new_spreadsheet_task(spreadsheet_pk):
    try:
        spreadsheet = StateSpreadsheet.objects.filter_active().get(pk=spreadsheet_pk)
    except StateSpreadsheet.DoesNotExist:
        return None

    try:
        ready, errors = spreadsheet.link_to_matching_spreadsheet_peer()
    except OnlyOneSpreadsheetException:
        notify_new_spreadsheet(spreadsheet)

    if ready:
        spreadsheet.import_to_final_dataset()
    else:
        notify_spreadsheet_mismatch(spreadsheet, errors)
