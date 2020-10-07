from collections import namedtuple
from functools import lru_cache
from itertools import groupby

import rows
import rows.utils

from brazil_data.util import load_csv_from_url

POPULATION_CSV_URL = (
    "https://raw.githubusercontent.com/turicas/covid19-br/master/data/populacao-por-municipio-2020.csv"  # noqa
)
POPULATION_SCHEMA_URL = (
    "https://raw.githubusercontent.com/turicas/covid19-br/master/schema/populacao-por-municipio.csv"  # noqa
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


def brazilian_cities_per_state():
    data = ibge_data_per_state()
    return {state: [city.city for city in state_cities] for state, state_cities in data.items()}


@lru_cache(maxsize=11140)
def normalize_city_name(name):
    # Simple normalization
    name = rows.fields.slug(name)
    for value in ("_de_", "_da_", "_do_", "_das_", "_dos_"):
        name = name.replace(value, "_")

    # Exceptions
    name = name.replace("_thome_", "_tome_")  # São Tomé das Letras
    if name == "florinia":
        name = "florinea"

    return name


@lru_cache(maxsize=1)
def normalized_ibge_data_per_state():
    data = ibge_data_per_state()
    new = {}
    for state, cities in data.items():
        new[state] = {normalize_city_name(city.city): city for city in cities}
    return new


@lru_cache(maxsize=11140)
def is_same_city(state, city_a, city_b):
    return normalize_city_name(city_a) == normalize_city_name(city_b)


@lru_cache(maxsize=5570)
def get_city_info(city, state):
    state = state.upper()
    data = normalized_ibge_data_per_state()
    return data[state][normalize_city_name(city)]


def get_state_info(state):
    data = ibge_data_per_state()
    try:
        city = data[state.upper()][0]
    except KeyError:
        return None
    # TODO: use brazil_data.states.STATES
    return StateInfo(state=city.state, state_ibge_code=city.state_ibge_code)
