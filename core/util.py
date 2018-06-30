import csv
import gc
import gzip
import io
import lzma
from textwrap import dedent

import django.db.models.fields
from django.db import connection, reset_queries, transaction
from django.db.utils import ProgrammingError
from rows.plugins.utils import ipartition
from core.models import Table


def get_fobj(filename, encoding=None):
    if filename.endswith('.gz'):
        fobj = gzip.GzipFile(filename, mode='rb')
    elif filename.endswith('.xz'):
        fobj = lzma.open(filename, mode='rb')
    else:
        if encoding is None:
            return open(filename, mode='rb')
        else:
            return open(filename, encoding=encoding)

    if encoding is None:
        return fobj
    else:
        return io.TextIOWrapper(fobj, encoding=encoding)


def create_object(Model, data):
    special_fields = (
        django.db.models.fields.DateField,
        django.db.models.fields.DateTimeField,
        django.db.models.fields.DecimalField,
    )

    for field in Model._meta.fields:
        if (isinstance(field, special_fields) and
            not (data.get(field.name) or '').strip()):
            data[field.name] = None

    return Model(**data)


def detect_column_sizes(filename, encoding='utf-8'):
    reader = csv.DictReader(get_fobj(filename, encoding))
    max_sizes = {}
    for row in reader:
        for key, value in row.items():
            max_sizes[key] = max(max_sizes.get(key, 0), len(value))
    return max_sizes


def get_company_by_document(document):
    Documents = Table.objects.for_dataset('documentos-brasil').named('documents').get_model()
    doc_prefix = document[:8]
    headquarter_prefix = doc_prefix + '0001'
    branches = Documents.objects.filter(
        docroot=doc_prefix,
        document_type='CNPJ',
    )
    if not branches.exists():
        # no document found with this prefix - we don't know this company
        raise Documents.DoesNotExist()

    try:
        obj = branches.get(document=document)
    except Documents.DoesNotExist:
        # document not found, but a branch or HQ exists
        try:
            obj = branches.get(document__startswith=headquarter_prefix)
        except Documents.DoesNotExist:
            # there's no HQ, but a branch exists
            obj = branches[0]

    else:
        # document found - let's check if there's a HQ
        if not document.startswith(headquarter_prefix):
            try:
                obj = branches.get(document__startswith=headquarter_prefix)
            except Documents.DoesNotExist:
                # there's no HQ, but the object was found anyway
                pass

    return obj
