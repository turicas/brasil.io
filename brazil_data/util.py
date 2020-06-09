from pathlib import Path

import rows
import rows.utils


def load_csv_from_url(data_url, schema_url):
    schema_filename = "schema-" + Path(schema_url).name
    data_filename = "data-" + Path(data_url).name
    if not Path(schema_filename).exists():
        rows.utils.download_file(schema_url, filename=schema_filename)
    if not Path(data_filename).exists():
        rows.utils.download_file(data_url, filename=data_filename)

    schema = rows.utils.load_schema(schema_filename)
    return rows.import_from_csv(data_filename, encoding="utf-8", force_types=schema)


def row_to_column(data):
    """Transform a list of dicts into a dict of lists (used to save some space)"""

    keys, all_keys = None, None
    for row in data:
        row_keys = set(row.keys())
        if keys is None:
            keys = {key: [] for key in row_keys}
            all_keys = set(keys.keys())
        for key in row_keys:
            if key not in keys:
                raise ValueError(f"Key {repr(key)}")
            keys[key].append(row[key])
        for key in all_keys - row_keys:
            keys[key].append(None)
    return keys
