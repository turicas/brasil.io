from django.dispatch import Signal, receiver

from covid19.models import StateSpreadsheet
from covid19.tasks import process_new_spreadsheet_task

new_spreadsheet_imported_signal = Signal(providing_args=["spreadsheet"])


@receiver(new_spreadsheet_imported_signal, dispatch_uid="new_import")
def process_new_spreadsheet_receiver(sender, spreadsheet, **kwargs):
    StateSpreadsheet.objects.cancel_older_versions(spreadsheet)
    process_new_spreadsheet_task.delay(spreadsheet_pk=spreadsheet.pk)
