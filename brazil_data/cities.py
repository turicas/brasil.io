from collections import namedtuple
from functools import lru_cache
from itertools import groupby

import rows
import rows.utils

from brazil_data.util import load_csv_from_url

POPULATION_CSV_URL = (
    "https://raw.githubusercontent.com/turicas/covid19-br/master/data/populacao-estimada-2019.csv"  # noqa
)
POPULATION_SCHEMA_URL = (
    "https://raw.githubusercontent.com/turicas/covid19-br/master/schema/populacao-estimada-2019.csv"  # noqa
)
StateInfo = namedtuple("StateInfo", ["state", "state_ibge_code"])


@lru_cache(maxsize=1)
def extract_ibge_data():
    return load_csv_from_url(POPULATION_CSV_URL, POPULATION_SCHEMA_URL)


@lru_cache(maxsize=1)
def ibge_data_per_state():
    data = extract_ibge_data()
    cities = sorted(data, key=lambda row: (row.state, rows.fields.slug(row.city)))
    return {
        state: [city for city in state_cities] for state, state_cities in groupby(cities, key=lambda row: row.state)
    }


def normalize_city_name(city):
    city = rows.fields.slug(city)
    for word in ("da", "das", "de", "do", "dos"):
        city = city.replace(f"_{word}_", "_")
    return city


def brazilian_cities_per_state():
    data = ibge_data_per_state()
    return {state: [city.city for city in state_cities] for state, state_cities in data.items()}


def get_city_info(city, state):
    data = ibge_data_per_state()
    try:
        norm_city = normalize_city_name(city)
        return {normalize_city_name(c.city): c for c in data[state.upper()]}[norm_city]
    except (KeyError, IndexError):
        return None


def get_state_info(state):
    data = ibge_data_per_state()
    try:
        city = data[state.upper()][0]
    except KeyError:
        return None
    # TODO: use brazil_data.states.STATES
    return StateInfo(state=city.state, state_ibge_code=city.state_ibge_code)
