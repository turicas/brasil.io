import csv
import io
import lzma
import shlex
import subprocess
import time

import rows
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.utils import ProgrammingError
from django.utils import timezone
from tqdm import tqdm

from core.models import Field, Table
from core.util import get_fobj


class Command(BaseCommand):
    help = 'Import data to Brasil.IO database'

    def add_arguments(self, parser):
        parser.add_argument('dataset_slug')
        parser.add_argument('tablename')
        parser.add_argument('filename')
        parser.add_argument('--no-input', required=False, action='store_true')
        parser.add_argument('--no-vacuum', required=False, action='store_true')
        parser.add_argument('--no-create-filter-indexes', required=False, action='store_true')
        parser.add_argument('--no-fill-choices', required=False, action='store_true')
        parser.add_argument('--no-create-search-index', required=False, action='store_true')

    def handle(self, *args, **kwargs):
        dataset_slug = kwargs['dataset_slug']
        tablename = kwargs['tablename']
        filename = kwargs['filename']
        ask_confirmation = not kwargs['no_input']
        vacuum = not kwargs['no_vacuum']
        create_filter_indexes = not kwargs['no_create_filter_indexes']
        fill_choices = not kwargs['no_fill_choices']
        create_search_index = not kwargs['no_create_search_index']

        if ask_confirmation:
            print(
                'This operation will DESTROY the existing data for this '
                'dataset table.'
            )
            answer = input('Do you want to continue? (y/n) ')
            if answer.lower().strip() not in ('y', 'yes'):
                exit()

        # Get the model and create the table if not exists
        table = Table.objects.for_dataset(dataset_slug).named(tablename)
        Model = table.get_model()
        with transaction.atomic():
            try:
                Model.delete_table()
            except ProgrammingError:  # Does not exist
                pass
            finally:
                Model.create_table(create_indexes=False)

        # Get file object, header and set command to run
        table_name = Model._meta.db_table
        encoding = 'utf-8'  # TODO: receive as a parameter
        batch_size = 50000  # TODO: receive as a paramenter
        timeout = 0.1
        fobj = get_fobj(filename)
        first_line = next(fobj).decode(encoding).strip()
        # TODO: get database_url in another way
        db = settings.DATABASES['default']
        database_url = ("postgres://{user}:{password}@{host}:{port}/{name}"
                        .format(user=db['USER'], password=db['PASSWORD'],
                                host=db['HOST'], port=db['PORT'],
                                name=db['NAME']))
        command = ('psql -c "\copy {table_name} ({first_line}) FROM STDIN '
                             'DELIMITER \',\' '
                             'QUOTE \'\\"\' '
                             'ENCODING \'{encoding}\' '
                             'CSV;" '
                        '"{database_url}"'
                   .format(table_name=table_name, first_line=first_line,
                           database_url=database_url, encoding=encoding))
        start = time.time()
        rows_imported = 0
        error = None
        with tqdm(desc='Importing data', unit='bytes', unit_scale=True,
                  unit_divisor=1024) as progress:
            try:
                process = subprocess.Popen(
                    shlex.split(command),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                finished = False
                chunk_size = 8388608  # 8MiB
                while not finished:
                    data = fobj.read(chunk_size)
                    if data == b'':
                        finished = True
                    else:
                        progress.update(process.stdin.write(data))
                stdout, stderr = process.communicate()
                if stderr != b'':
                    error = stderr
                else:
                    rows_imported = int(stdout.replace(b'COPY ', b'').strip())
            except BrokenPipeError:
                error = process.stderr.read()
        end = time.time()
        duration = end - start
        if error:
            print('ERROR: {}'.format(error.decode('utf-8')))
            exit(1)
        else:
            table.last_update = timezone.now()
            table.save()
            print('  done in {:.3f}s ({} rows imported, {:.3f} rows/s).'
                  .format(duration, rows_imported, rows_imported / duration))

        if vacuum:
            print('Running VACUUM ANALYSE...', end='', flush=True)
            start = time.time()
            Model.analyse_table()
            end = time.time()
            print('  done in {:.3f}s.'.format(end - start))

        if create_filter_indexes:
            # TODO: warn if field has_choices but not in Table.filtering
            print('Creating filter indexes...', end='', flush=True)
            start = time.time()
            Model.create_indexes()
            end = time.time()
            print('  done in {:.3f}s.'.format(end - start))

        if fill_choices:
            print('Filling choices...')
            start = time.time()
            choiceables = Field.objects.for_table(table).choiceables()
            for field in choiceables:
                print('  {}'.format(field.name), end='', flush=True)
                start_field = time.time()
                field.update_choices()
                field.save()
                end_field = time.time()
                print(' - done in {:.3f}s.'.format(end_field - start_field))
            end = time.time()
            print('  done in {:.3f}s.'.format(end - start))

        if create_search_index:
            print('Updating search index...', end='', flush=True)
            start = time.time()
            Model.objects.update_search_index()
            end = time.time()
            print('  done in {:.3f}s.'.format(end - start))
