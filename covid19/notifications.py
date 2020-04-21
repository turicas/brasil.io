import io
import rows
from functools import lru_cache
import requests


COLLABORATORS_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI/export?format=csv&id=1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI&gid=0"


@lru_cache(maxsize=1)
def collaborators_data():
    response = requests.get(COLLABORATORS_SPREADSHEET_URL)
    url_table = rows.import_from_csv(io.BytesIO(response.content), encoding="utf-8")
    return url_table


def get_state_row(state):
    data = collaborators_data()
    return [r for r in data if r.uf.upper() == state.upper()][0]


def notify_new_spreadsheet(spreadsheet):
    raise NotImplementedError


def notify_spreadsheet_mismatch(spreadsheet, errors):
    raise NotImplementedError
