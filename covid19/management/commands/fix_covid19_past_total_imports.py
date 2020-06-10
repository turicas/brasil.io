from django.core.management.base import BaseCommand

from covid19.models import StateSpreadsheet


class Command(BaseCommand):
    help = "Fix previous inconsisted cancelled spreadsheets"

    def handle(self, *args, **kwargs):
        only_with_total_qs = StateSpreadsheet.objects.filter(
            data__warnings__icontains="Planilha importada somente com dados totais"
        )

        updated = 0
        for sp in only_with_total_qs:
            previous_deployed = StateSpreadsheet.objects.exclude(id__gte=sp.id,).most_recent_deployed(sp.state, sp.date)
            if not previous_deployed:
                continue

            if sp.table_data_by_city != previous_deployed.table_data_by_city:
                updated += 1
                print(f"Planilha ({sp.id} em {sp.created_at}) somente com totais para {sp.state} - {sp.date}.", end=" ")
                print(
                    f"Usando números das cidades usando a planilha anterior ({previous_deployed.id} e {previous_deployed.created_at})."
                )

                sp.table_data = [sp.get_total_data()] + list(previous_deployed.table_data_by_city.values())
                sp.save()

        print("------")
        print(
            f"{only_with_total_qs.count()} planilhas somente com totais.\n{updated} tiveram os dados para múnicipios atualizados."
        )
