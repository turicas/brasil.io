from rows.fields import IntegerField

from brazil_data.cities import get_city_info, get_state_info

from covid19.exceptions import SpreadsheetValidationErrors
from covid19.models import StateSpreadsheet
from covid19.stats import Covid19Stats


TOTAL_LINE_DISPLAY = 'TOTAL NO ESTADO'
UNDEFINED_DISPLAY = 'Importados/Indefinidos'
INVALID_CITY_CODE = -1


def format_spreadsheet_rows_as_dict(rows_table, date, state):
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
        confirmed_attr = _get_column_name(
            field_names, ['confirmados', 'confirmado', 'casos_confirmados']
        )
    except ValueError as e:
        validation_errors.new_error(str(e))
    try:
        deaths_attr = _get_column_name(field_names, ['obitos', 'obito', 'morte', 'mortes'])
    except ValueError as e:
        validation_errors.new_error(str(e))
    try:
        city_attr = _get_column_name(field_names, ['municipio', 'cidade'])
    except ValueError as e:
        validation_errors.new_error(str(e))

    # can't check on field types if any invalid column
    validation_errors.raise_if_errors()

    if not rows_table.fields[confirmed_attr] == IntegerField:
        validation_errors.new_error('A coluna "Confirmados" precisa ter somente números inteiros"')
    if not rows_table.fields[deaths_attr] == IntegerField:
        validation_errors.new_error('A coluna "Mortes" precisa ter somente números inteiros"')

    results = []
    has_total, has_undefined = False, False
    total_cases, total_deaths = 0, 0
    sum_cases, sum_deaths = 0, 0
    for entry in rows_table:
        city = getattr(entry, city_attr, None)
        confirmed = getattr(entry, confirmed_attr, None)
        deaths = getattr(entry, deaths_attr, None)

        if (not confirmed and deaths) or (not deaths and confirmed):
            validation_errors.new_error(f'Dados de casos ou óbitos incompletos na linha {city}')
        if confirmed is None or deaths is None:
            continue

        if deaths > confirmed:
            validation_errors.new_error(
                f'Valor de óbitos maior que casos confirmados na linha {city} da planilha'
            )
        elif deaths < 0 or confirmed < 0:
            validation_errors.new_error(
                f'Valores negativos na linha {city} da planilha'
            )

        result = _parse_city_data(city, confirmed, deaths, date, state)
        if result['city_ibge_code'] == INVALID_CITY_CODE:
            validation_errors.new_error(f'{city} não pertence à UF {state}')
            continue

        if result['place_type'] == 'state':
            has_total = True
            total_cases, total_deaths = confirmed, deaths
        else:
            sum_cases += confirmed
            sum_deaths += deaths
            if result['city'] == UNDEFINED_DISPLAY:
                has_undefined = True

        results.append(result)

    if not has_total:
        validation_errors.new_error(f'A linha "{TOTAL_LINE_DISPLAY}" está faltando na planilha')
    if not has_undefined:
        validation_errors.new_error(f'A linha "{UNDEFINED_DISPLAY}" está faltando na planilha')

    if sum_cases and sum_cases != total_cases:
        validation_errors.new_error(
            f'A soma de casos ({sum_cases}) difere da entrada total ({total_cases}).'
        )
    if sum_deaths and sum_deaths != total_deaths:
        validation_errors.new_error(
            f'A soma de mortes ({sum_deaths}) difere da entrada total ({total_deaths}).'
        )

    validation_errors.raise_if_errors()

    # this is hacky, I know, but I wanted to centralize all kind of validations inside this function
    on_going_spreadsheet = StateSpreadsheet(state=state, date=date)
    on_going_spreadsheet.table_data = results
    return results, validate_historical_data(on_going_spreadsheet)


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
        data['city_ibge_code'] = get_state_info(state).state_ibge_code
        data['place_type'] = 'state'
        data['city'] = None
    elif city == UNDEFINED_DISPLAY:
        data['city_ibge_code'] = None
    else:
        city_info = get_city_info(city, state)
        data['city_ibge_code'] = getattr(city_info, 'city_ibge_code', INVALID_CITY_CODE)
        data['city'] = getattr(city_info, 'city', INVALID_CITY_CODE)

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
        return data['confirmed'] < previous.confirmed or data['deaths'] < previous.deaths

    warnings = []
    validation_errors = SpreadsheetValidationErrors()
    covid19_stats = Covid19Stats()

    city_entries = covid19_stats.most_recent_city_entries_for_state(spreadsheet.state, spreadsheet.date)
    state_entry = covid19_stats.most_recent_state_entry(spreadsheet.state, spreadsheet.date)

    for entry in city_entries:
        city_data = spreadsheet.get_data_from_city(entry.city_ibge_code)
        if not city_data:
            validation_errors.new_error(
                f"{entry.city} possui dados históricos e não está presente na planilha"
            )
            continue
        if lower_numbers(entry, city_data):
            warnings.append(
                f"Números de confirmados ou óbitos em {entry.city} é menor que o anterior."
            )

    total_data = spreadsheet.get_total_data()
    if lower_numbers(state_entry, total_data):
        warnings.append(
            f"Números de confirmados ou óbitos totais é menor que o total anterior."
        )

    validation_errors.raise_if_errors()
    return warnings
