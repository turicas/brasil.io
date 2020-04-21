from django_rq import job

from covid19.models import StateSpreadsheet


@job
def process_new_spreadsheet_task(spreadsheet_pk):
    try:
        spreadsheet = StateSpreadsheet.objects.filter_active().get(pk=spreadsheet_pk)
    except StateSpreadsheet.DoesNotExist:
        return None

    print(f'Async process {spreadsheet}...')
    # TODO https://github.com/turicas/brasil.io/issues/212
