from datetime import date

from django.core.management.base import BaseCommand

from covid19.models import StateSpreadsheet


class Command(BaseCommand):
    help = "Fix previous inconsisted cancelled spreadsheets"

    def handle(self, *args, **kwargs):
        start_date = date(2020, 6, 5)

        cancelled_spreadsheets = StateSpreadsheet.objects.filter(
            date__gte=start_date,
        ).filter_inactive().order_by('-id')


        for sp in cancelled_spreadsheets:
            same_spreadsheet_qs = StateSpreadsheet.objects.filter_active().filter(
                user=sp.user,
                state=sp.state,
                date=sp.date,
            ).exclude(pk=sp.pk)

            if same_spreadsheet_qs.exists():
                continue

            print(f"Planilha ({sp.id}) {sp.state} - {sp.date} (por {sp.user}) será reativada.", end=" ")
            sp.cancelled = False
            sp.save()

            if sp.deployed:
                print("Planilha deployed ativada.")
            elif sp.sibilings:
                ready, errors = sp.link_to_matching_spreadsheet_peer()
                if ready:
                    sp.import_to_final_dataset()
                    print(f"Ativada e atualizada para deployed com sucesso")
                else:
                    print(f"Ativada com erros de importação: {errors}")
            else:
                print(f'Ativada sem dados para dar match')
