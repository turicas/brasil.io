from functools import lru_cache
from itertools import groupby
from pathlib import Path

import rows
import rows.utils

POPULATION_CSV_URL = "https://raw.githubusercontent.com/turicas/covid19-br/master/data/populacao-estimada-2019.csv"  # noqa
POPULATION_SCHEMA_URL = "https://raw.githubusercontent.com/turicas/covid19-br/master/schema/populacao-estimada-2019.csv"  #noqa


@lru_cache(maxsize=1)
def brazilian_cities_per_state(
    schema_filename="schema-population.csv", population_filename="population.csv"
):
    if not Path(schema_filename).exists():
        rows.utils.download_file(POPULATION_SCHEMA_URL, filename=schema_filename)
    if not Path(population_filename).exists():
        rows.utils.download_file(POPULATION_CSV_URL, filename=population_filename)

    schema = rows.utils.load_schema(schema_filename)
    table = rows.import_from_csv(
        population_filename, encoding="utf-8", force_types=schema
    )
    cities = sorted(table, key=lambda row: (row.state, rows.fields.slug(row.city)))
    return {
        state: [city.city for city in state_cities]
        for state, state_cities in groupby(cities, key=lambda row: row.state)
    }
