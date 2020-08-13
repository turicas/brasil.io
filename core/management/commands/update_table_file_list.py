from django.core.management.base import BaseCommand

from core.commands import UpdateTableFileListCommand


class Command(BaseCommand):
    help = "Update HTML with links to dataset files"

    def add_arguments(self, parser):
        parser.add_argument("dataset_slug")

    def handle(self, *args, **kwargs):
        dataset_slug = kwargs["dataset_slug"]

        UpdateTableFileListCommand.execute(dataset_slug)
