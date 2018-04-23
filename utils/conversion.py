import csv
import gzip
import io
import lzma
import sqlite3

import rows


def open_compressed(filename, encoding, mode='r'):
    if filename.endswith('.xz'):
        return io.TextIOWrapper(
            lzma.open(filename, mode=mode),
            encoding=encoding,
        )

    elif filename.endswith('.gz'):
        return io.TextIOWrapper(
            gzip.GzipFile(filename, mode=mode),
            encoding=encoding,
        )

    else:
        return open(filename, encoding=encoding)


def csv2sqlite(input_filename, output_filename, table_name, samples=30000,
               batch_size=10000, encoding='utf-8', callback=None,
               force_types=None):

    # Identify data types
    fobj = open_compressed(input_filename, encoding)
    reader = csv.reader(fobj)
    header = next(reader)
    data = []
    for index, row in enumerate(reader):
        row = dict(zip(header, row))
        if index == samples:
            break
        data.append(row)
    fields = rows.import_from_dicts(data, import_fields=header).fields
    if force_types is not None:
        fields.update(force_types)

    # Create lazy table object to be converted
    table = rows.Table(fields=fields)
    reader = csv.reader(open_compressed(input_filename, encoding))
    next(reader)  # skip header
    table._rows = reader

    # Export to SQLite
    rows.export_to_sqlite(table, output_filename, table_name=table_name,
                          callback=callback, batch_size=batch_size)


def sqlite2csv(input_filename, table_name, output_filename, batch_size=10000,
               encoding='utf-8', callback=None):

    connection = sqlite3.Connection(input_filename)
    cursor = connection.cursor()
    result = cursor.execute('SELECT * FROM {}'.format(table_name))
    header = [item[0] for item in cursor.description]
    fobj = open_compressed(output_filename, encoding, mode='w')
    writer = csv.writer(fobj)
    writer.writerow(header)
    counter = 0
    for batch in rows.plugins.utils.ipartition(result, batch_size):
        writer.writerows(batch)
        counter += len(batch)
        if callback and counter % batch_size == 0:
            callback(counter)

    fobj.close()
