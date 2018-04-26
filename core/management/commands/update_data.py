import io
from urllib.request import urlopen

import rows
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from core.models import Dataset, Link, Version, Table, Field


DATASETS, VERSIONS, TABLES = {}, {}, {}

def is_empty(row):
    return not any([str(value).strip()
                    for value in row._asdict().values()
                    if value is not None])

def is_complete(row):
    return all([str(value).strip()
                for key, value in row._asdict().items()
                if key not in ('options', 'link_template')])

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
        TABLES[key] = Table.objects.get(dataset=dataset, version=version,
                                        name=name)
    return TABLES[key]

def dataset_update_data(row):
    return {
        'slug': row['slug'],
        'defaults': row,
    }

def link_update_data(row):
    return {
        'dataset': row['dataset'],
        'url': row['url'],
        'defaults': row,
    }

def version_update_data(row):
    return {
        'dataset': row['dataset'],
        'download_url': row['download_url'],
        'name': row['name'],
        'defaults': row,
    }


def str_to_list(data):
    if data:
        return [field.strip() for field in data.split(',')]


def table_update_data(row):
    row['ordering'] = str_to_list(row['ordering'])
    row['filtering'] = str_to_list(row['filtering'])
    row['search'] = str_to_list(row['search'])
    return {
        'dataset': row['dataset'],
        'version': row['version'],
        'name': row['name'],
        'defaults': row,
    }

def field_update_data(row):
    return {
        'dataset': row['dataset'],
        'version': row['version'],
        'table': row['table'],
        'name': row['name'],
        'defaults': row,
    }


class Command(BaseCommand):
    help = 'Update models (metadata only)'

    def _update_data(self, cls, table, get_update_data):
        print('Updating {}...'.format(cls.__name__), end='', flush=True)
        total_created, total_updated, total_skipped = 0, 0, 0
        for row in table:
            if is_empty(row):
                continue
            elif not is_complete(row):
                total_skipped += 1
                continue

            data = row._asdict()
            try:
                if 'dataset_slug' in data:
                    data['dataset'] = get_dataset(data.pop('dataset_slug'))
                if 'version_name' in data:
                    data['version'] = get_version(data['dataset'],
                                                  data.pop('version_name'))
                if 'table_name' in data:
                    data['table'] = get_table(data['dataset'],
                                              data['version'],
                                              data.pop('table_name'))
            except ObjectDoesNotExist:
                total_skipped += 1
                continue

            _, created = cls.objects.update_or_create(
                **get_update_data(data)
            )
            if created:
                total_created += 1
            else:
                total_updated += 1
        print(' created: {}, updated: {}, skipped: {}.'
              .format(total_created, total_updated, total_skipped))

    def handle(self, *args, **kwargs):
        self.datasets, self.tables, self.versions = {}, {}, {}
        response = urlopen(settings.DATA_URL)
        data = response.read()

        update_functions = [
            (Dataset, dataset_update_data),
            (Link, link_update_data),
            (Version, version_update_data),
            (Table, table_update_data),
            (Field, field_update_data),
        ]
        for Model, update_data_function in update_functions:
            table = rows.import_from_xlsx(
                io.BytesIO(data),
                sheet_name=Model.__name__,
            )
            self._update_data(Model, table, update_data_function)
