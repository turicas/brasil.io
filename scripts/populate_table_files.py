from itertools import chain

import requests

from core.commands import UpdateTableFileCommand
from core.models import Dataset


def run():
    """
    $ python manage.py runscript populate_table_files
    """
    not_found = []
    all_tables = chain(*[d.tables for d in Dataset.objects.all()])

    for table in all_tables:
        ds_slug = table.dataset.slug
        file_url = f"https://data.brasil.io/dataset/{ds_slug}/{table.name}.csv.gz"

        response = requests.head(file_url)
        if not response.ok:
            not_found.append(table)
            continue

        UpdateTableFileCommand.execute(ds_slug, table.name, file_url, delete_source=False)
        print("-" * 10)

    if not_found:
        print("#" * 20)
        print("Couldn't find .csv.gz file with default paths for the following tables:")
        for not_found_table in not_found:
            print(f"- {not_found_table}")
