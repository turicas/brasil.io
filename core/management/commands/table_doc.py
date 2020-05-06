from django.core.management.base import BaseCommand

from core.models import Table
from core.util import create_table_documentation


class Command(BaseCommand):
    help = "Create table documentation automatically"

    def add_arguments(self, parser):
        parser.add_argument("dataset_slug")
        parser.add_argument("table_name")

    def handle(self, *args, **kwargs):
        dataset_slug = kwargs["dataset_slug"]
        table_name = kwargs["table_name"]
        table = Table.with_hidden.get(dataset__slug=dataset_slug, name=table_name)
        print(create_table_documentation(table))
