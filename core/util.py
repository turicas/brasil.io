import csv
import gzip
import io
import lzma
from textwrap import dedent

import django.db.models.fields
from django.db import connection
from django.db import connection, models
from rows.plugins.utils import ipartition

from core import dynamic_models


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


def import_file(filename, Model, encoding='utf-8', batch_size=5000):
    reader = csv.DictReader(get_fobj(filename, encoding))
    counter = 0
    for batch in ipartition(reader, batch_size):
        Model.objects.bulk_create([create_object(Model, data) for data in batch])
        counter += len(batch)
        print(counter)
    connection.commit()


def detect_column_sizes(filename, encoding='utf-8'):
    reader = csv.DictReader(get_fobj(filename, encoding))
    max_sizes = {}
    for row in reader:
        for key, value in row.items():
            max_sizes[key] = max(max_sizes.get(key, 0), len(value))
    return max_sizes


def create_tables():
    # TODO: must get all tables from database (core.Table model)
    # TODO: check if table/index already created before trying to create it
    # TODO: indices must be expressed as meta-data and automatically
    # created
    SociosBrasil = dynamic_models.register['socios-brasil']
    fields = [(f.name, f) for f in SociosBrasil._meta.local_fields]
    table_name = SociosBrasil._meta.db_table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(SociosBrasil)
    with connection.cursor() as cursor:
        # TODO: get index info from ordering
        cursor.execute(dedent('''
            CREATE INDEX idx_core_sociosbrasil
            ON core_sociosbrasil
            (cnpj_empresa ASC, nome_socio ASC);
        '''))
        # TODO: get fts fields info from filtering
        cursor.execute(dedent('''
            CREATE INDEX idx_core_sociosbrasil_text
            ON core_sociosbrasil
            USING GIN (to_tsvector('portuguese', cnpj_empresa || ' ' || nome_empresa || ' ' || nome_socio));
        '''))

    GastosDiretos = dynamic_models.register['gastos-diretos']
    fields = [(f.name, f) for f in GastosDiretos._meta.local_fields]
    table_name = GastosDiretos._meta.db_table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(GastosDiretos)
    with connection.cursor() as cursor:
        cursor.execute(dedent('''
            CREATE INDEX idx_core_gastosdiretos
            ON core_gastosdiretos
            (data_pagamento DESC, nome_favorecido ASC);
        '''))
        cursor.execute(dedent('''
            CREATE INDEX idx_core_gastosdiretos_text
            ON core_gastosdiretos
            USING GIN (to_tsvector('portuguese', nome_orgao_superior || ' ' || nome_unidade_gestora || ' ' || nome_grupo_despesa || ' ' || nome_elemento_despesa || ' ' || nome_funcao || ' ' || nome_subfuncao || ' ' || codigo_favorecido || ' ' || nome_favorecido));
        '''))
