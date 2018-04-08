import time

from django.core.management.base import BaseCommand

from core.models import Dataset
from core.util import import_file


def print_count(counter):
    print(counter)


class Command(BaseCommand):
    help = 'Import data to Brasil.IO database'

    def add_arguments(self, parser):
        parser.add_argument(
            'slug',
            choices=Dataset.objects.all().values_list('slug', flat=True),
        )
        parser.add_argument('filename')

    def handle(self, *args, **kwargs):
        slug = kwargs['slug']
        filename = kwargs['filename']

        start = time.time()
        dataset = Dataset.objects.get(slug=slug)
        total = import_file(
            filename,
            dataset.get_last_data_model(),
            callback=print_count,
        )
        end = time.time()
        print('Total time:', end - start)
