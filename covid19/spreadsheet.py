import io
from urllib.parse import parse_qs, urlparse

import rows
from cachetools import cached, TTLCache

from brazil_data.cities import brazilian_cities_per_state
from core.util import http_get
from covid19.models import StateSpreadsheet


STATE_LINKS_SPREADSHEET_ID = "1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI"
FIELDS_BOLETIM = {
    "date": rows.fields.DateField,
    "url": rows.fields.TextField,
    "notes": rows.fields.TextField,
}


def spreadsheet_download_url(url_or_id, file_format):
    if url_or_id.startswith("http"):
        spreadsheet_id = parse_qs(urlparse(url_or_id).query)["id"][0]
    else:
        spreadsheet_id = url_or_id
    return f"https://docs.google.com/spreadsheets/u/0/d/{spreadsheet_id}/export?format={file_format}&id={spreadsheet_id}"


@cached(cache=TTLCache(maxsize=100, ttl=24 * 3600))
def get_general_spreadsheet(timeout=5):
    data = http_get(
        spreadsheet_download_url(STATE_LINKS_SPREADSHEET_ID, "csv"), timeout
    )
    table = rows.import_from_csv(io.BytesIO(data), encoding="utf-8")
    return {row.uf: row for row in table}


def get_state_data_from_google_spreadsheets(state, timeout=5):
    general_spreadsheet = get_general_spreadsheet()
    state_spreadsheet_url = general_spreadsheet[state].planilha_brasilio
    state_spreadsheet_download_url = spreadsheet_download_url(
        state_spreadsheet_url, "xlsx"
    )
    data = http_get(state_spreadsheet_download_url, timeout)
    reports = rows.import_from_xlsx(
        io.BytesIO(data), sheet_name="Boletins (FINAL)", force_types=FIELDS_BOLETIM
    )
    cases = rows.import_from_xlsx(io.BytesIO(data), sheet_name="Casos (FINAL)")
    return {
        "reports": [dict(row._asdict()) for row in reports if row.date],
        "cases": [dict(row._asdict()) for row in cases if row.municipio]
    }


def get_state_spreadsheets_from_database(state):
    # TODO: this function could be refactored as QuerySet methods
    statuses = {text: number for (number, text) in StateSpreadsheet.STATUS_CHOICES}
    return StateSpreadsheet.objects.from_state(state).filter(
        status=statuses["deployed"]
    ).order_by("-created_at")  # get the newest first


def get_state_data_from_db(state):
    """Return all state cases from DB, grouped by date"""

    spreadsheets = get_state_spreadsheets_from_database(state)

    cases, reports = {}, []
    for spreadsheet in spreadsheets:
        date = spreadsheet.date
        for url in spreadsheet.boletim_urls:
            # TODO: what to do when we add the same URL twice (from 2 equal
            # spreadsheets)?
            reports.append(
                {
                    "date": date,
                    "url": url,
                    "notes": spreadsheet.boletim_notes,
                }
            )

        if date in cases:
            continue  # Other spreadsheet for the same date already did it
        cases[date] = {}
        for row in spreadsheet.data["table"]:
            city = row["city"]
            if city is None:
                city = "TOTAL NO ESTADO"
            cases[date][city] = {
                "confirmed": row["confirmed"],
                "deaths": row["deaths"],
            }

    return {
        "reports": reports,
        "cases": cases,
    }


def merge_state_data(state):
    # Get data from Google Spreadsheets and DB
    gs_data = get_state_data_from_google_spreadsheets(state)
    original_reports = gs_data["reports"]
    original_cases = gs_data["cases"]
    db_data = get_state_data_from_db(state)
    new_reports = db_data["reports"]
    new_cases = db_data["cases"]

    # Update original reports (GS) with new ones (DB), removing GS reports for
    # dates which show up in DB.
    new_reports_dates = set(row["date"] for row in new_reports)
    original_reports_filtered = [
        row
        for row in original_reports
        if row["date"] not in new_reports_dates
    ]
    final_reports = original_reports_filtered + new_reports

    # Update original cases (GS) with new ones (DB), overwritting GS cases for
    # dates which show up in DB.
    final_cases = []
    for row in original_cases:
        # TODO: check if city names are correct from GS?
        row = row.copy()
        city = row["municipio"]
        for date, values_for_date in new_cases.items():
            date_str = f"{date.day:02d}_{date.month:02d}"
            city_on_date = values_for_date.get(city, {})
            row[f"confirmados_{date_str}"] = city_on_date.get("confirmed", None)
            row[f"mortes_{date_str}"] = city_on_date.get("deaths", None)
        final_cases.append(row)

    return {
        "reports": final_reports,
        "cases": final_cases
    }

def create_merged_state_spreadsheet(state):
    state_data = merge_state_data(state)
    reports = rows.import_from_dicts(state_data["reports"])
    cases = rows.import_from_dicts(state_data["cases"])

    data = io.BytesIO()
    rows.export_to_xlsx(reports, data, sheet_name="Boletins (FINAL)")
    data.seek(0)
    rows.export_to_xlsx(cases, data, sheet_name="Casos (FINAL)")
    data.seek(0)
    return data


if __name__ == "__main__":
    # XXX: Run this on `manage.py shell`:
    from covid19.spreadsheet import create_merged_state_spreadsheet
    data = create_merged_state_spreadsheet("AC")
    with open("acre.xlsx", mode="wb") as fobj:
       fobj.write(data.read())
