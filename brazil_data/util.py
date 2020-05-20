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
