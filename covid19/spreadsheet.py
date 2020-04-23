import io

import rows

from brazil_data.cities import get_city_info

from covid19 import google_data
from covid19.models import StateSpreadsheet
from covid19.spreadsheet_validator import TOTAL_LINE_DISPLAY, UNDEFINED_DISPLAY
from covid19.exceptions import SpreadsheetValidationErrors


def get_state_data_from_db(state):
    """Return all state cases from DB, grouped by date"""
    cases, reports = {}, []
    for spreadsheet in StateSpreadsheet.objects.deployable_for_state(state):
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

        cases[date] = {}
        for row in spreadsheet.data["table"]:
            city = row["city"]
            if city is None:
                city = TOTAL_LINE_DISPLAY
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
    original_data_errors = SpreadsheetValidationErrors()
    for row in original_cases:
        row = row.copy()
        city = row["municipio"]
        if city not in [TOTAL_LINE_DISPLAY, UNDEFINED_DISPLAY]:
            city_info = get_city_info(city, state)
            if city_info:
                city = city_info.city
            else:
                msg = f'Nome inválido de cidade "{city}" na planilha do Google.'
                original_data_errors.new_error(msg)

        for date, values_for_date in new_cases.items():
            date_str = f"{date.day:02d}_{date.month:02d}"
            city_on_date = values_for_date.get(city, {})
            row[f"confirmados_{date_str}"] = city_on_date.get("confirmed", None)
            row[f"mortes_{date_str}"] = city_on_date.get("deaths", None)
        final_cases.append(row)

    original_data_errors.raise_if_errors()
    return {
        "reports": final_reports,
        "cases": final_cases
    }


def create_merged_state_spreadsheet(state):
    state_data = merge_state_data(state)
    reports = rows.import_from_dicts(state_data["reports"])
    cases = rows.import_from_dicts(state_data["cases"])

    data = io.BytesIO()
    rows.export_to_xlsx(reports, data, sheet_name=google_data.BOLETIM_SPREADSHEET)
    data.seek(0)
    rows.export_to_xlsx(cases, data, sheet_name=google_data.CASOS_SPREADSHEET)
    data.seek(0)
    return data


if __name__ == "__main__":
    # XXX: Run this on `manage.py shell`:
    from covid19.spreadsheet import create_merged_state_spreadsheet
    data = create_merged_state_spreadsheet("AC")
    with open("acre.xlsx", mode="wb") as fobj:
        fobj.write(data.read())
