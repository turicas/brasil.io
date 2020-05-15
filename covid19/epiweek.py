from functools import lru_cache

from brazil_data.util import load_csv_from_url

EPIWEEK_CSV_URL = "https://raw.githubusercontent.com/turicas/covid19-br/master/data/epidemiological-week.csv"  # noqa
EPIWEEK_SCHEMA_URL = (
    "https://raw.githubusercontent.com/turicas/covid19-br/master/schema/epidemiological-week.csv"  # noqa
)


@lru_cache(maxsize=1)
def extract_epiweek_data():
    return {
        row.date: (row.epidemiological_year, row.epidemiological_week)
        for row in load_csv_from_url(EPIWEEK_CSV_URL, EPIWEEK_SCHEMA_URL)
    }


@lru_cache(maxsize=365)
def get_epiweek(date):
    return extract_epiweek_data()[date]
