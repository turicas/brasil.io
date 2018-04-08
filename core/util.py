import csv
import gc
import gzip
import io
import lzma

import django.db.models.fields
from django.db import connection, reset_queries
from django.db.utils import ProgrammingError
from rows.plugins.utils import ipartition


def get_fobj(filename, encoding):
    if filename.endswith('.gz'):
        fobj = gzip.GzipFile(filename)
    elif filename.endswith('.xz'):
        fobj = lzma.open(filename)
    else:
        raise RuntimeError('File type not known')

    return io.TextIOWrapper(fobj, encoding=encoding)


def create_object(Model, data):
    for field in Model._meta.fields:
        if isinstance(field, django.db.models.fields.DateField):
            if not (data.get(field.name) or '').strip():
                data[field.name] = None
    return Model(**data)


def import_file(filename, Model, encoding='utf-8', batch_size=5000,
                callback=None):
    try:
        Model.delete_table()
    except ProgrammingError:  # Does not exist
        pass
    finally:
        Model.create_table()

    reader = csv.DictReader(get_fobj(filename, encoding))
    counter = 0
    for batch in ipartition(reader, batch_size):
        Model.objects.bulk_create([create_object(Model, data)
                                   for data in batch])
        counter += len(batch)
        reset_queries()  # Tip from https://stackoverflow.com/a/29924044
        gc.collect()
        if callback:
            callback(counter)
    if callback:
        callback(counter)

    connection.commit()
    return counter


def detect_column_sizes(filename, encoding='utf-8'):
    reader = csv.DictReader(get_fobj(filename, encoding))
    max_sizes = {}
    for row in reader:
        for key, value in row.items():
            max_sizes[key] = max(max_sizes.get(key, 0), len(value))
    return max_sizes
