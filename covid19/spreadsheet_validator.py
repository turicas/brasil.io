from rows.fields import IntegerField

from brazil_data.cities import get_city_info, get_state_info
from covid19.exceptions import SpreadsheetValidationErrors
from covid19.models import StateSpreadsheet
from covid19.stats import Covid19Stats

TOTAL_LINE_DISPLAY = "TOTAL NO ESTADO"
UNDEFINED_DISPLAY = "Importados/Indefinidos"
INVALID_CITY_CODE = -1


def format_spreadsheet_rows_as_dict(rows_table, date, state, skip_sum_cases=False, skip_sum_deaths=False):
    """
    Receives rows.Table object, a date and a brazilan UF, validates the data
    and returns tuble with 2 lists:
        - valid and formated results data
        - warnings about the data

    This is an auxiliary method used by covid19.forms.StateSpreadsheetForm with the uploaded file
    """
    validation_errors = SpreadsheetValidationErrors()
    field_names = rows_table.field_names

    try:
        confirmed_attr = _get_column_name(field_names, ["confirmados", "confirmado", "casos_confirmados"])
    except ValueError as e:
        validation_errors.new_error(str(e))
    try:
        deaths_attr = _get_column_name(field_names, ["obitos", "obito", "morte", "mortes"])
    except ValueError as e:
        validation_errors.new_error(str(e))
    try:
        city_attr = _get_column_name(field_names, ["municipio", "cidade"])
    except ValueError as e:
        validation_errors.new_error(str(e))

    # can't check on field types if any invalid column
    validation_errors.raise_if_errors()

    if not rows_table.fields[confirmed_attr] == IntegerField:
        validation_errors.new_error('A coluna "Confirmados" precisa ter somente números inteiros"')
    if not rows_table.fields[deaths_attr] == IntegerField:
        validation_errors.new_error('A coluna "Mortes" precisa ter somente números inteiros"')

    results, warnings = [], []
    has_total, has_undefined = False, False
    total_cases, total_deaths = 0, 0
    sum_cases, sum_deaths = 0, 0
    processed_cities = set()
    for entry in rows_table:
        city = getattr(entry, city_attr, None)
        confirmed = getattr(entry, confirmed_attr, None)
        deaths = getattr(entry, deaths_attr, None)
        if not city:
            if confirmed or deaths:
                msg = "Uma ou mais linhas com a coluna de cidade vazia possuem números de confirmados ou óbitos"
                validation_errors.new_error(msg)
            continue

        if city in processed_cities:
            validation_errors.new_error(f"Mais de uma entrada para {city}")

        processed_cities.add(city)
        is_undefined = city == UNDEFINED_DISPLAY
        if is_undefined:
            has_undefined = True
        elif city == TOTAL_LINE_DISPLAY:
            has_total = True

        if (confirmed is None and deaths is not None) or (deaths is None and confirmed is not None):
            validation_errors.new_error(f"Dados de casos ou óbitos incompletos na linha {city}")
        if confirmed is None or deaths is None:
            continue

        try:
            if deaths > confirmed:
                if is_undefined:
                    warnings.append(f"{city} com número óbitos maior que de casos confirmados.")
                else:
                    msg = f"Valor de óbitos maior que casos confirmados na linha {city} da planilha"
                    validation_errors.new_error(msg)
            elif deaths < 0 or confirmed < 0:
                validation_errors.new_error(f"Valores negativos na linha {city} da planilha")
        except TypeError:
            validation_errors.new_error(f"Provavelmente há uma fórmula na linha {city} da planilha")
            continue

        result = _parse_city_data(city, confirmed, deaths, date, state)
        if result["city_ibge_code"] == INVALID_CITY_CODE:
            validation_errors.new_error(f"{city} não pertence à UF {state}")
            continue

        if result["place_type"] == "state":
            total_cases, total_deaths = confirmed, deaths
        else:
            sum_cases += confirmed
            sum_deaths += deaths

        results.append(result)

    if not has_total:
        validation_errors.new_error(f'A linha "{TOTAL_LINE_DISPLAY}" está faltando na planilha')
    if not has_undefined and len(results) > 1:
        validation_errors.new_error(f'A linha "{UNDEFINED_DISPLAY}" está faltando na planilha')

    if skip_sum_cases:
        warnings.append("A checagem da soma de casos por cidade com o valor total foi desativada.")
    elif sum_cases and sum_cases != total_cases:
        validation_errors.new_error(f"A soma de casos ({sum_cases}) difere da entrada total ({total_cases}).")
    if skip_sum_deaths:
        warnings.append("A checagem da soma de óbitos por cidade com o valor total foi desativada.")
    elif sum_deaths and sum_deaths != total_deaths:
        validation_errors.new_error(f"A soma de mortes ({sum_deaths}) difere da entrada total ({total_deaths}).")

    validation_errors.raise_if_errors()

    # this is hacky, I know, but I wanted to centralize all kind of validations inside this function
    on_going_spreadsheet = StateSpreadsheet(state=state, date=date)
    on_going_spreadsheet.table_data = results
    warnings.extend(validate_historical_data(on_going_spreadsheet))
    return on_going_spreadsheet.table_data, warnings


def _parse_city_data(city, confirmed, deaths, date, state):
    data = {
        "city": city,
        "confirmed": confirmed,
        "date": date.isoformat(),
        "deaths": deaths,
        "place_type": "city",
        "state": state,
    }

    if city == TOTAL_LINE_DISPLAY:
        data["city_ibge_code"] = get_state_info(state).state_ibge_code
        data["place_type"] = "state"
        data["city"] = None
    elif city == UNDEFINED_DISPLAY:
        data["city_ibge_code"] = None
    else:
        city_info = get_city_info(city, state)
        data["city_ibge_code"] = getattr(city_info, "city_ibge_code", INVALID_CITY_CODE)
        data["city"] = getattr(city_info, "city", INVALID_CITY_CODE)

    return data


def _get_column_name(field_names, options):
    # XXX: this function expects all keys already in lowercase and slugified by `rows` library
    valid_columns = [key for key in field_names if key in options]
    if not valid_columns:
        raise ValueError(f"A coluna '{options[0]}' não existe")
    elif len(valid_columns) > 1:
        raise ValueError(f"Foi encontrada mais de uma coluna possível para '{options[0]}'")
    return valid_columns[0]


def validate_historical_data(spreadsheet):
    """
    Validate the spreadsheet against historical data in the database.
    If any invalid data, it'll raise a SpreadsheetValidationErrors
    If valid data, returns a list with eventual warning messages
    """

    def lower_numbers(previous, data):
        if not previous:
            return False
        return data["confirmed"] < previous["confirmed"] or data["deaths"] < previous["deaths"]

    warnings = []
    clean_results = spreadsheet.table_data
    validation_errors = SpreadsheetValidationErrors()
    Covid19Stats()
    s_date = spreadsheet.date
    has_only_total = False
    total_data = spreadsheet.get_total_data()
    if len(spreadsheet.table_data) == 1 and total_data:
        has_only_total = True

    city_entries, state_entry = [], {}
    most_recent = StateSpreadsheet.objects.most_recent_deployed(spreadsheet.state, spreadsheet.date)
    if most_recent:
        state_entry = most_recent.get_total_data()
        city_entries = most_recent.table_data_by_city.values()

    for entry in city_entries:
        city_data = spreadsheet.get_data_from_city(entry["city_ibge_code"])
        if not has_only_total and not city_data and (entry["confirmed"] or entry["deaths"]):
            validation_errors.new_error(f"{entry['city']} possui dados históricos e não está presente na planilha.")
            continue
        elif not city_data:  # previous entry for the city has 0 deaths and 0 confirmed
            data = _parse_city_data(entry["city"], entry["confirmed"], entry["deaths"], s_date, entry["state"])
            clean_results.append(data)
            if not has_only_total:
                warnings.append(
                    f"{entry['city']} possui dados históricos zerados/nulos, não presente na planilha e foi adicionado."
                )
        elif lower_numbers(entry, city_data):
            warnings.append(f"Números de confirmados ou óbitos em {entry['city']} é menor que o anterior.")

    if has_only_total:
        if state_entry:
            warnings.append(
                f"{StateSpreadsheet.ONLY_WITH_TOTAL_WARNING} Dados de cidades foram reutilizados da importação do dia {state_entry['date']}."
            )
        else:
            warnings.append(StateSpreadsheet.ONLY_WITH_TOTAL_WARNING)

    if lower_numbers(state_entry, total_data):
        warnings.append("Números de confirmados ou óbitos totais é menor que o total anterior.")

    validation_errors.raise_if_errors()

    spreadsheet.table_data = clean_results
    return warnings
