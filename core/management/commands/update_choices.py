import time

from django.core.management.base import BaseCommand
from django.db.utils import ProgrammingError

from core.models import Dataset, Field, Table


class Command(BaseCommand):
    help = "Update choices cache"

    def add_arguments(self, parser):
        parser.add_argument("--dataset-slug", required=False, action="store")
        parser.add_argument("--tablename", required=False, action="store")

    def handle(self, *args, **kwargs):
        dataset_slug = kwargs["dataset_slug"]
        tablename = kwargs["tablename"]

        datasets = Dataset.objects.all()
        if dataset_slug:
            datasets = datasets.filter(slug=dataset_slug)

        for dataset in datasets.iterator():
            print("{}".format(dataset.slug))
            start_dataset = time.time()

            tables = Table.with_hidden.for_dataset(dataset)
            if tablename:
                tables = [tables.named(tablename)]
            for table in tables:
                print("  {}".format(table.name))
                start_table = time.time()

                choiceables = Field.objects.for_table(table).choiceables()
                for field in choiceables:
                    start = time.time()
                    print("    {}... ".format(field.name), end="", flush=True)
                    try:
                        field.update_choices()
                        field.save()
                    except ProgrammingError:
                        print("ERROR: model does not exist.")
                    else:
                        end = time.time()
                        print("done in {:7.3f}s.".format(end - start))

                end_table = time.time()
                print("    table done in {:7.3f}s.".format(end_table - start_table))

            end_dataset = time.time()
            print("  dataset done in {:7.3f}s.".format(end_dataset - start_dataset))
