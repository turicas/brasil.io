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
from tqdm import tqdm

from core.models import Dataset
from core.util import get_fobj


class Command(BaseCommand):
    help = 'Import data to Brasil.IO database'

    def add_arguments(self, parser):
        parser.add_argument('slug')
        parser.add_argument('filename')
        # TODO: create a way to import other tables

    def handle(self, *args, **kwargs):
        slug = kwargs['slug']
        filename = kwargs['filename']

        # Get the model and create the table
        dataset = Dataset.objects.get(slug=slug)
        Model = dataset.get_last_data_model()
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
            print('ERROR:', error)
        else:
            print('  done in {:.3f}s ({} rows imported, {:.3f} rows/s).'
                  .format(duration, rows_imported, rows_imported / duration))
        # TODO: do not continue if error
        # TODO: add flags for each action

        print('Running VACUUM ANALYSE...', end='', flush=True)
        start = time.time()
        Model.analyse_table()
        end = time.time()
        print('  done in {:.3f}s.'.format(end - start))

        # TODO: warn if field has_choices but not in Table.filtering
        print('Creating indexes...', end='', flush=True)
        start = time.time()
        Model.create_indexes()
        end = time.time()
        print('  done in {:.3f}s.'.format(end - start))

        print('Updating search index...', end='', flush=True)
        start = time.time()
        Model.objects.update_search_index()
        end = time.time()
        print('  done in {:.3f}s.'.format(end - start))
