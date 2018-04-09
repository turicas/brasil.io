import lzma
import shlex
import subprocess
import time

from django.core.management.base import BaseCommand
from django.conf import settings

from core.models import Dataset, DYNAMIC_MODEL_REGISTRY
from core.util import import_file, get_fobj


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

        # Get the model and create the table
        dataset = Dataset.objects.get(slug=slug)
        Model = dataset.get_last_data_model()
        try:
            Model.delete_table()
        except ProgrammingError:  # Does not exist
            pass
        finally:
            # TODO: do not create indexes
            Model.create_table()

        # Get file object, header and call `psql`
        table_name = Model._meta.db_table
        fobj = get_fobj(filename)
        encoding = 'utf-8'
        first_line = next(fobj).decode(encoding).strip()
        db = settings.DATABASES['default']
        # TODO: get database_url in another wat
        database_url = f"postgres://{db['USER']}:{db['PASSWORD']}@{db['HOST']}:{db['PORT']}/{db['NAME']}"
        # TODO: change encoding based on file encoding (receive as parameter)
        command = f'''psql -c "\copy {table_name} ({first_line}) FROM STDIN DELIMITER ',' CSV HEADER ENCODING 'utf8';" "{database_url}"'''
        process = subprocess.Popen(
            shlex.split(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for index, line in enumerate(fobj, start=1):
            process.stdin.write(line)
            if index % 1000 == 0:
                print(index)
        print(index)
        process.communicate()

        end = time.time()
        print('Total time:', end - start)
