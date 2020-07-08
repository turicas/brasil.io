from datetime import date

from django.core.management.base import BaseCommand

from core.commands import ImportDataCommand


class Command(BaseCommand):
    help = "Import data to Brasil.IO database"

    def add_arguments(self, parser):
        parser.add_argument("dataset_slug")
        parser.add_argument("tablename")
        parser.add_argument("filename")
        parser.add_argument("--no-input", required=False, action="store_true")
        parser.add_argument("--no-import-data", required=False, action="store_true")
        parser.add_argument("--no-vacuum", required=False, action="store_true")
        parser.add_argument("--no-clear-view-cache", required=False, action="store_true")
        parser.add_argument("--no-create-filter-indexes", required=False, action="store_true")
        parser.add_argument("--no-fill-choices", required=False, action="store_true")
        parser.add_argument("--no-clean-after", required=False, action="store_true")
        parser.add_argument(
            "--collect-date", required=False, action="store", help="collect date in format YYYY-MM-DD",
        )

    def clean_collect_date(self, collect_date):
        if not collect_date:
            return None

        year, month, day = [int(v) for v in collect_date.split("-")]
        return date(year, month, day)

    def handle(self, *args, **kwargs):
        dataset_slug = kwargs["dataset_slug"]
        tablename = kwargs["tablename"]
        filename = kwargs["filename"]
        ask_confirmation = not kwargs["no_input"]
        import_data = not kwargs["no_import_data"]
        vacuum = not kwargs["no_vacuum"]
        clear_view_cache = not kwargs["no_clear_view_cache"]
        create_filter_indexes = not kwargs["no_create_filter_indexes"]
        fill_choices = not kwargs["no_fill_choices"]
        clean_after = not kwargs["no_clean_after"]
        collect_date = self.clean_collect_date(kwargs["collect_date"])

        if ask_confirmation:
            print("This operation will DESTROY the existing data for this " "dataset table.")
            answer = input("Do you want to continue? (y/n) ")
            if answer.lower().strip() not in ("y", "yes"):
                exit()

        ImportDataCommand.execute(
            dataset_slug,
            tablename,
            filename,
            import_data=import_data,
            vacuum=vacuum,
            clear_view_cache=clear_view_cache,
            create_filter_indexes=create_filter_indexes,
            fill_choices=fill_choices,
            clean_after=clean_after,
            collect_date=collect_date,
        )
