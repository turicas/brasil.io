from django.core.management import call_command
from django.core.management.base import BaseCommand

from core.commands import UpdateTableFileCommand


class Command(BaseCommand):
    help = "Update table's complete data file"

    def add_arguments(self, parser):
        parser.add_argument("dataset_slug")
        parser.add_argument("tablename")
        parser.add_argument("file_url")
        parser.add_argument(
            "--delete-source", required=False, action="store_true", help="delete source Minio file (default False)"
        )
        parser.add_argument(
            "--update-list", required=False, action="store_true", help="update dataset _meta/list.html (default False)"
        )
        parser.add_argument(
            "--collect-date", required=False, action="store", help="collect date in format YYYY-MM-DD",
        )

    def handle(self, *args, **kwargs):
        dataset_slug = kwargs["dataset_slug"]
        tablename = kwargs["tablename"]
        file_url = kwargs["file_url"]
        update_list = kwargs["update_list"]

        UpdateTableFileCommand.execute(
            dataset_slug, tablename, file_url, delete_source=kwargs["delete_source"],
        )
        if update_list:
            call_command("update_table_file_list", dataset_slug, collect_date=kwargs["collect_date"])
