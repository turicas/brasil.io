from django.core.management.base import BaseCommand

from core.models import Dataset, DataTable


class Command(BaseCommand):
    help = "Deleta tabelas com dados definidas pelas entradas de DataTable inativas"

    def add_arguments(self, parser):
        parser.add_argument("--only", help="Execute comando apenas para esses datasets (separados por vírgula)")

    def handle(self, *args, **kwargs):
        only = kwargs["only"] or ""
        specific_datasets = [i for i in only.split(",") if i.strip()]
        for ds in Dataset.objects.all():
            if specific_datasets and ds.slug not in specific_datasets:
                continue

            qs = DataTable.objects.for_dataset(ds.slug).inactive()
            print(f"Deleting old data from {qs.count()} DataTable entries for {ds.slug} dataset...")
            for data_table in qs:
                data_table.delete_data_table()
