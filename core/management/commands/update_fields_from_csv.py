import rows
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Dataset, Field, Table, Version


class Command(BaseCommand):
    help = "Create fields from CSV"

    def add_arguments(self, parser):
        parser.add_argument("csv_filename")

    def handle(self, *args, **kwargs):
        csv_filename = kwargs["csv_filename"]
        table = rows.import_from_csv(csv_filename, force_types={"options": rows.fields.JSONField})
        expected_fieldset = set(
            "dataset_slug description frontend_filter has_choices "
            "link_template order null name options obfuscate show "
            "show_on_frontend table_name title type version_name searchable".split()
        )
        fieldset = set(table.field_names)
        if fieldset != expected_fieldset:
            raise ValueError(f"Field names didn't match ({fieldset - expected_fieldset} / {expected_fieldset - fieldset})")

        with transaction.atomic():
            fields_to_save, tables_created = [], []
            for row in table:
                # First pass: get objects from database: won't add Field here,
                # since if there are errors, the script will raise exception inside
                # this first `for`.
                row = row._asdict()
                row["version_name"] = str(row["version_name"])
                row["dataset"], _ = Dataset.objects.get_or_create(slug=row.pop("dataset_slug"), defaults={"show": True})
                row["version"], _ = Version.objects.get_or_create(
                    dataset=row["dataset"],
                    name=row.pop("version_name"),
                    defaults={"collected_at": timezone.now(), "order": 1},
                )
                row["table"], table_created = Table.with_hidden.get_or_create(
                    dataset=row["dataset"],
                    version=row["version"],
                    name=row.pop("table_name"),
                    defaults={"default": False, "ordering": ["id"], "search_fields": []},
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
                fields_to_save.append((action, field))
                if table_created:
                    tables_created.append(row["table"])

            for table in tables_created:
                table.search_fields = [
                    field.name
                    for action, field in fields_to_save
                    if field.table == table and field.type in ("text", "string")
                ]
                table.save()

            for action, field in fields_to_save:
                print(f"{action}: {field}")
                field.save()
