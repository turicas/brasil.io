import rows
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Dataset, Field, Table, Version


class Command(BaseCommand):
    help = "Create fields from CSV"

    def add_arguments(self, parser):
        parser.add_argument("csv_filename")

    def handle(self, *args, **kwargs):
        csv_filename = kwargs["csv_filename"]
        table = rows.import_from_csv(csv_filename)
        expected_field_names = set(
            "dataset_slug description frontend_filter has_choices "
            "link_template order null name options obfuscate show "
            "show_on_frontend table_name title type version_name".split()
        )
        if set(table.field_names) != expected_field_names:
            raise ValueError("Field names didn't match")

        with transaction.atomic():
            fields_to_add = []
            for row in table:
                # First pass: get objects from database: won't add Field here,
                # since if there are errors, the script will raise exception inside
                # this first `for`.
                row = row._asdict()
                row["version_name"] = str(row["version_name"])
                row["dataset"] = Dataset.objects.get(slug=row.pop("dataset_slug"))
                row["version"] = Version.objects.get(dataset=row["dataset"], name=row.pop("version_name"))
                row["table"] = Table.with_hidden.get(
                    dataset=row["dataset"], version=row["version"], name=row.pop("table_name"),
                )
                existing_field = Field.objects.filter(
                    dataset=row["dataset"], version=row["version"], table=row["table"], name=row["name"],
                )
                if not existing_field.exists():
                    action = "created"
                    field = Field(**row)
                else:
                    action = "updated"
                    field = existing_field.first()
                    for key, value in row.items():
                        if key in ("dataset", "version", "table"):
                            continue
                        setattr(field, key, value)
                fields_to_add.append((action, field))

            for action, field in fields_to_add:
                print(f"{action}: {field}")
                field.save()
