import rows
from django.core.management.base import BaseCommand

from core.models import Dataset


class Command(BaseCommand):
    help = "Create CSV fields file based on metadata stored on database"

    def add_arguments(self, parser):
        parser.add_argument("--dataset-slug")
        parser.add_argument("--table-name")
        parser.add_argument("csv_filename")

    def handle(self, *args, **kwargs):
        filter_dataset_slug = kwargs["dataset_slug"]
        filter_table_name = kwargs["table_name"]
        csv_filename = kwargs["csv_filename"]
        writer = rows.utils.CsvLazyDictWriter(csv_filename)

        datasets = Dataset.objects.all()
        if filter_dataset_slug:
            datasets = datasets.filter(slug=filter_dataset_slug)

        for dataset in datasets:
            dataset_slug = dataset.slug
            tables = dataset.all_tables
            if filter_table_name:
                tables = tables.filter(name=filter_table_name)

            for table in tables:
                table_name = table.name
                version_name = table.version.name
                for field in table.fields:
                    writer.writerow(
                        {
                            "dataset_slug": dataset_slug,
                            "description": field.description,
                            "searchable": field.searchable,
                            "frontend_filter": field.frontend_filter,
                            "has_choices": field.has_choices,
                            "link_template": field.link_template,
                            "order": field.order,
                            "null": field.null,
                            "name": field.name,
                            "options": rows.fields.JSONField.serialize(field.options),
                            "obfuscate": field.obfuscate,
                            "show": field.show,
                            "show_on_frontend": field.show_on_frontend,
                            "table_name": table_name,
                            "title": field.title,
                            "type": field.type,
                            "version_name": version_name,
                        }
                    )
