from django_rq import job

from covid19.exceptions import OnlyOneSpreadsheetException
from covid19.models import StateSpreadsheet
from covid19.notifications import notify_new_spreadsheet, notify_spreadsheet_mismatch, notify_import_success


@job
def process_new_spreadsheet_task(spreadsheet_pk):
    try:
        spreadsheet = StateSpreadsheet.objects.filter_active().get(pk=spreadsheet_pk)
    except StateSpreadsheet.DoesNotExist:
        print(f"No active spreadsheet with pk ({spreadsheet_pk}).")
        return None

    state, date = spreadsheet.state, spreadsheet.date

    print(f"Processing new spreadsheet for {state} on {date}.")
    try:
        ready, errors = spreadsheet.link_to_matching_spreadsheet_peer()
    except OnlyOneSpreadsheetException:
        print(f"First spreadsheet for {state} on {date}. Sending notifications for a peer review.")
        notify_new_spreadsheet(spreadsheet)
        return

    if ready:
        print(f"Spreadsheet {spreadsheet.id} for {state} on {date} is valid! Starting import process.")
        spreadsheet.import_to_final_dataset(notify_import_success)
    else:
        print(f"Spreadsheet {spreadsheet.id} for {state} on {date} didn't validate.")
        notify_spreadsheet_mismatch(spreadsheet, errors)
