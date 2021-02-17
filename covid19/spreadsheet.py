from brazil_data.cities import get_city_info
from covid19 import google_data
from covid19.exceptions import SpreadsheetValidationErrors
from covid19.models import StateSpreadsheet
from covid19.spreadsheet_validator import TOTAL_LINE_DISPLAY, UNDEFINED_DISPLAY


def fix_key(key):
    """
    >>> fix_key("municipio")
    'municipio'
    >>> fix_key("confirmados_17_03")
    'confirmados_2020-03-17'
    >>> fix_key("mortes_02_03")
    'mortes_2020-03-02'
    """
    if key == "municipio":
        return key

    label, day, month = key.split("_")
    return f"{label}_2020-{month}-{day}"


def merge_state_data(state):
    gs_data = google_data.get_base_data()[state]  # Get data from old Google Spreadsheets
    original_reports = gs_data["reports"]
    # Fix format of old data from Google Spreadsheets (add year to date)
    original_cases = [
        {fix_key(key): value for key, value in city_cases.items() if not key.startswith("field_")}
        for city_cases in gs_data["cases"]
    ]

    db_data = StateSpreadsheet.objects.get_state_data(state)  # Get data from database
    new_reports = db_data["reports"]
    new_cases = db_data["cases"]

    # Update original reports (GS) with new ones (DB), removing GS reports for
    # dates which show up in DB.
    new_reports_dates = set(row["date"] for row in new_reports)
    original_reports_filtered = [row for row in original_reports if row["date"] not in new_reports_dates]
    final_reports = original_reports_filtered + new_reports

    # Update original cases (GS) with new ones (DB), overwritting GS cases for
    # dates which show up in DB.
    final_cases = []
    original_data_errors = SpreadsheetValidationErrors()
    original_cities = set()
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

        original_cities.add(city)
        for date, values_for_date in new_cases.items():
            date_str = date.isoformat()  # YYYY-MM-DD
            city_on_date = values_for_date.get(city, {})
            row[f"confirmados_{date_str}"] = city_on_date.get("confirmed", None)
            row[f"mortes_{date_str}"] = city_on_date.get("deaths", None)
        final_cases.append(row)

    # recent IBGE data can add new cities that weren't present in the original data
    new_rows = {}
    for date, values_for_date in new_cases.items():
        date_str = date.isoformat()  # YYYY-MM-DD
        for city, data in values_for_date.items():
            city_info = get_city_info(city, state)
            if city_info:
                city = city_info.city

            if city in original_cities:
                continue
            elif city not in new_rows:
                new_rows[city] = {"municipio": city}

            row = new_rows[city]
            row[f"confirmados_{date_str}"] = data.get("confirmed", None)
            row[f"mortes_{date_str}"] = data.get("deaths", None)

    if new_rows:
        final_cases.extend(new_rows.values())

    ordered_cases = []
    for row in final_cases:
        row = row_with_sorted_columns(row)
        city_info = get_city_info(row["municipio"], state)
        if city_info:
            row["municipio"] = city_info.city
        ordered_cases.append(row)

    original_data_errors.raise_if_errors()
    return {"reports": final_reports, "cases": ordered_cases}


def row_with_sorted_columns(row):
    row_dates = set(key.split("_")[1] for key in row.keys() if key.startswith("confirmados_"))

    new = {"municipio": row["municipio"]}
    for date_str in sorted(row_dates, reverse=True):
        year, month, day = date_str.split("-")
        confirmed = f"confirmados_{date_str}"
        deaths = f"mortes_{date_str}"
        new[confirmed] = row[confirmed]
        new[deaths] = row[deaths]

    return new
