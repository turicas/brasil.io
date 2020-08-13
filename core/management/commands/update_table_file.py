from django.core.management.base import BaseCommand

from core.commands import UpdateTableFileCommand


class Command(BaseCommand):
    help = "Update table's complete data file"

    def add_arguments(self, parser):
        parser.add_argument("dataset_slug")
        parser.add_argument("tablename")
        parser.add_argument("file_url")

    def handle(self, *args, **kwargs):
        dataset_slug = kwargs["dataset_slug"]
        tablename = kwargs["tablename"]
        file_url = kwargs["file_url"]

        UpdateTableFileCommand.execute(
            dataset_slug,
            tablename,
            file_url,
        )