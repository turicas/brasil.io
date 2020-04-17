from collections import namedtuple
from functools import lru_cache
from itertools import groupby
from pathlib import Path

import rows
import rows.utils

POPULATION_CSV_URL = "https://raw.githubusercontent.com/turicas/covid19-br/master/data/populacao-estimada-2019.csv"  # noqa
POPULATION_SCHEMA_URL = "https://raw.githubusercontent.com/turicas/covid19-br/master/schema/populacao-estimada-2019.csv"  # noqa
StateInfo = namedtuple("StateInfo", ['state', 'state_ibge_code'])


@lru_cache(maxsize=1)
def extract_ibge_data(schema_filename, population_filename):
    if not Path(schema_filename).exists():
        rows.utils.download_file(POPULATION_SCHEMA_URL, filename=schema_filename)
    if not Path(population_filename).exists():
        rows.utils.download_file(POPULATION_CSV_URL, filename=population_filename)

    schema = rows.utils.load_schema(schema_filename)
    return rows.import_from_csv(
        population_filename, encoding="utf-8", force_types=schema
    )


@lru_cache(maxsize=1)
def ibge_data_per_state(schema_filename, population_filename):
    data = extract_ibge_data(schema_filename, population_filename)
    cities = sorted(data, key=lambda row: (row.state, rows.fields.slug(row.city)))
    return {
        state: [city for city in state_cities]
        for state, state_cities in groupby(cities, key=lambda row: row.state)
    }


def brazilian_cities_per_state(
    schema_filename="schema-population.csv", population_filename="population.csv"
):
    data = ibge_data_per_state(schema_filename, population_filename)
    return {
        state: [city.city for city in state_cities]
        for state, state_cities in data.items()
    }


def get_city_info(
        city, state, schema_filename="schema-population.csv", population_filename="population.csv"
):
    data = ibge_data_per_state(schema_filename, population_filename)
    try:
        cities = data[state.upper()]
        return [c for c in cities if c.city.lower() == city.lower()][0]
    except (KeyError, IndexError):
        return None


def get_state_info(
    state, schema_filename="schema-population.csv", population_filename="population.csv"
):
    data = ibge_data_per_state(schema_filename, population_filename)
    try:
        city = data[state.upper()][0]
    except KeyError:
        return None
    return StateInfo(state=city.state, state_ibge_code=city.state_ibge_code)
