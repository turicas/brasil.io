import io

import rows

from brazil_data.cities import brazilian_cities_per_state
from core.util import http_get

from covid19 import google_data
from covid19.models import StateSpreadsheet


def get_state_data_from_db(state):
    """Return all state cases from DB, grouped by date"""

    spreadsheets = StateSpreadsheet.objects.deployed().from_state(state).most_recent_first()

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
    gs_data = google_data.get_state_data_from_google_spreadsheets(state)
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
