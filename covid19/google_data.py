import io
import rows
from cache_memoize import cache_memoize
from collections import namedtuple
from retry import retry
from urllib.parse import parse_qs, urlparse

from core.util import http_get


STATE_LINKS_SPREADSHEET_ID = "1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI"
FIELDS_BOLETIM = {
    "date": rows.fields.DateField,
    "url": rows.fields.TextField,
    "notes": rows.fields.TextField,
}
BOLETIM_SPREADSHEET = "Boletins (FINAL)"
CASOS_SPREADSHEET = "Casos (FINAL)"


def spreadsheet_download_url(url_or_id, file_format):
    if url_or_id.startswith("http"):
        spreadsheet_id = parse_qs(urlparse(url_or_id).query)["id"][0]
    else:
        spreadsheet_id = url_or_id
    return (
        f"https://docs.google.com/spreadsheets/u/0/d/{spreadsheet_id}/export?format={file_format}&id={spreadsheet_id}"
    )


@cache_memoize(24 * 3600)
def get_general_spreadsheet(timeout=5):
    data = http_get(spreadsheet_download_url(STATE_LINKS_SPREADSHEET_ID, "csv"), timeout)
    table = rows.import_from_csv(io.BytesIO(data), encoding="utf-8")
    return {row.uf: row._asdict() for row in table}


def import_info_by_state(state):
    states_data = get_general_spreadsheet()
    data = states_data[state.upper()]
    StateData = namedtuple("StateData", data.keys())
    return StateData(**data)


@retry(tries=3, delay=5)
def get_state_data_from_google_spreadsheets(state, timeout=5):
    state_spreadsheet_url = import_info_by_state(state).planilha_brasilio
    state_spreadsheet_download_url = spreadsheet_download_url(state_spreadsheet_url, "xlsx")
    data = http_get(state_spreadsheet_download_url, timeout)
    reports = rows.import_from_xlsx(io.BytesIO(data), sheet_name=BOLETIM_SPREADSHEET, force_types=FIELDS_BOLETIM)
    cases = rows.import_from_xlsx(io.BytesIO(data), sheet_name=CASOS_SPREADSHEET)
    return {
        "reports": [dict(row._asdict()) for row in reports if row.date],
        "cases": [dict(row._asdict()) for row in cases if row.municipio],
    }
