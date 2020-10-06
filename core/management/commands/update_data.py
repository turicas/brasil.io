import io

import rows
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from core.models import Dataset, DataTable, Field, Link, Table, Version
from core.util import http_get

DATASETS, VERSIONS, TABLES = {}, {}, {}


def is_empty(row):
    return not any([str(value).strip() for value in row._asdict().values() if value is not None])


def is_complete(row):
    return all(
        [
            str(value).strip()
            for key, value in row._asdict().items()
            if key not in ("options", "link_template", "description")
        ]
    )


def get_dataset(slug):
    if slug not in DATASETS:
        DATASETS[slug] = Dataset.objects.get(slug=slug)
    return DATASETS[slug]


def get_version(dataset, name):
    key = (dataset.id, name)
    if key not in VERSIONS:
        VERSIONS[key] = Version.objects.get(dataset=dataset, name=name)
    return VERSIONS[key]


def get_table(dataset, version, name):
    key = (dataset.id, version.id, name)
    if key not in TABLES:
        TABLES[key] = Table.with_hidden.get(dataset=dataset, version=version, name=name)
    return TABLES[key]


def dataset_update_data(row):
    return {"slug": row["slug"], "defaults": row}


def link_update_data(row):
    return {"dataset": row["dataset"], "url": row["url"], "defaults": row}


def version_update_data(row):
    return {"dataset": row["dataset"], "name": row["name"], "defaults": row}


def str_to_list(data):
    if data:
        return [field.strip() for field in data.split(",")]


def table_update_data(row):
    row["ordering"] = str_to_list(row["ordering"])
    row["filtering_fields"] = str_to_list(row["filtering"])
    row["search"] = str_to_list(row["search"])
    return {"dataset": row["dataset"], "version": row["version"], "name": row["name"], "defaults": row}


def field_update_data(row):
    return {
        "dataset": row["dataset"],
        "version": row["version"],
        "table": row["table"],
        "name": row["name"],
        "defaults": row,
    }


class Command(BaseCommand):
    help = "Update models (metadata only)"

    def _update_data(self, cls, table, get_update_data):
        print("Updating {}...".format(cls.__name__), end="", flush=True)
        total_created, total_updated, total_skipped = 0, 0, 0
        for row in table:
            if is_empty(row):
                continue
            elif not is_complete(row):
                total_skipped += 1
                continue

            data = row._asdict()
            try:
                if "dataset_slug" in data:
                    data["dataset"] = get_dataset(data.pop("dataset_slug"))
                if "version_name" in data:
                    data["version"] = get_version(data["dataset"], data.pop("version_name"))
                if "table_name" in data:
                    data["table"] = get_table(data["dataset"], data["version"], data.pop("table_name"))
            except ObjectDoesNotExist:
                total_skipped += 1
                continue

            _, created = cls.objects.update_or_create(**get_update_data(data))
            if created:
                total_created += 1
            else:
                total_updated += 1
        print(" created: {}, updated: {}, skipped: {}.".format(total_created, total_updated, total_skipped))

    def add_arguments(self, parser):
        parser.add_argument("--truncate", action="store_true")

    def handle(self, *args, **kwargs):
        truncate = kwargs.get("truncate", False)
        update_functions = [
            (Dataset, dataset_update_data),
            (Link, link_update_data),
            (Version, version_update_data),
            (Table, table_update_data),
            (Field, field_update_data),
        ]

        data_tables_map = {}
        for table in Table.with_hidden.all():
            key = (table.dataset.slug, table.name)
            data_tables_map[key] = table.data_table

        if truncate:
            print("Deleting metadata to create new objects...")
            for Model, _ in update_functions:
                Model.objects.all().delete()
        else:
            print(
                "WARNING: updating data only. If some field was removed "
                "this change will not be reflected on your database. "
                "Consider using --truncate"
            )

        self.datasets, self.tables, self.versions = {}, {}, {}
        response_data = http_get(settings.DATA_URL, 5)
        if response_data is None:
            raise RuntimeError(f"Cannot download {settings.DATA_URL}")
        for Model, update_data_function in update_functions:
            table = rows.import_from_xlsx(
                io.BytesIO(response_data), sheet_name=Model.__name__, workbook_kwargs={"read_only": False}
            )
            self._update_data(Model, table, update_data_function)

        print("Updating DataTable...", end="", flush=True)
        total_created, total_updated, total_skipped = 0, 0, 0
        for table in Table.with_hidden.select_related("dataset"):
            key = (table.dataset.slug, table.name)
            data_table = data_tables_map.get(key, None)
            if data_table is None:  # create DataTable if new Table or if previous was None
                data_table = DataTable.new_data_table(table, suffix_size=0)
                data_table.activate()
                total_created += 1
            elif data_table.table != table:  # Tables were truncated so previous DataTables get updated
                total_updated += 1
                data_table.table = table
                data_table.save()
            else:  # Same table as before, so no need to update
                total_skipped += 1

            if table.filtering_fields:  # avoid None
                table.fields.filter(name__in=table.filtering_fields).update(frontend_filter=True)

        print(" created: {}, updated: {}, skipped: {}.".format(total_created, total_updated, total_skipped))
