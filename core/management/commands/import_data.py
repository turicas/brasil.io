import os
import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import ProgrammingError
from django.utils import timezone
from rows.utils import pgimport

from core.models import Field, Table


class Command(BaseCommand):
    help = 'Import data to Brasil.IO database'

    def add_arguments(self, parser):
        parser.add_argument('dataset_slug')
        parser.add_argument('tablename')
        parser.add_argument('filename')
        parser.add_argument('--no-input', required=False, action='store_true')
        parser.add_argument('--no-import-data', required=False, action='store_true')
        parser.add_argument('--no-vacuum', required=False, action='store_true')
        parser.add_argument('--no-create-filter-indexes', required=False, action='store_true')
        parser.add_argument('--no-fill-choices', required=False, action='store_true')
        parser.add_argument('--no-create-search-index', required=False, action='store_true')

    def handle(self, *args, **kwargs):
        dataset_slug = kwargs['dataset_slug']
        tablename = kwargs['tablename']
        filename = kwargs['filename']
        ask_confirmation = not kwargs['no_input']
        import_data = not kwargs['no_import_data']
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

        table = Table.objects.for_dataset(dataset_slug).named(tablename)
        Model = table.get_model()

        if import_data:
            # Create the table if not exists
            with transaction.atomic():
                try:
                    Model.delete_table()
                except ProgrammingError:  # Does not exist
                    pass
                finally:
                    Model.create_table(create_indexes=False)

            # Get file object, header and set command to run
            table_name = Model._meta.db_table
            database_uri = os.environ['DATABASE_URL']
            encoding = 'utf-8'  # TODO: receive as a parameter
            timeout = 0.1  # TODO: receive as a parameter
            start_time = time.time()
            try:
                rows_imported = pgimport(
                    filename=filename,
                    encoding=encoding,
                    database_uri=database_uri,
                    table_name=table_name,
                    create_table=False,
                    timeout=timeout,
                    progress=True,
                )
            except RuntimeError as exception:
                print('ERROR: {}'.format(exception.args[0]))
                exit(1)
            else:
                table.last_update = timezone.now()
                table.save()
                end_time = time.time()
                duration = end_time - start_time
                print('  done in {:7.3f}s ({} rows imported, {:.3f} rows/s).'
                      .format(duration, rows_imported, rows_imported / duration))
            Model = table.get_model(cache=False)

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
