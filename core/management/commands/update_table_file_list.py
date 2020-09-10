from datetime import datetime

from django.core.management.base import BaseCommand

from core.commands import UpdateTableFileListCommand


class Command(BaseCommand):
    help = "Update HTML with links to dataset files"

    def add_arguments(self, parser):
        parser.add_argument("dataset_slug")
        parser.add_argument(
            "--collect-date", required=False, action="store", help="collect date in format YYYY-MM-DD",
        )

    def clean_collect_date(self, collect_date):
        if not collect_date:
            return None

        return datetime.strptime(collect_date, "%Y-%m-%d").date()

    def handle(self, *args, **kwargs):
        dataset_slug = kwargs["dataset_slug"]
        collect_date = self.clean_collect_date(kwargs["collect_date"])

        UpdateTableFileListCommand.execute(dataset_slug, collect_date=collect_date)
