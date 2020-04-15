from rows.fields import IntegerField

from django.forms import ValidationError

from brazil_data.cities import get_city_info, get_state_info


TOTAL_LINE_DISPLAY = 'TOTAL NO ESTADO'
UNDEFINED_DISPLAY = 'Importados/Indefinidos'
INVALID_CITY_CODE = -1


class SpreadsheetValidationErrors(Exception):
    """
    Custom exception to hold all error messages raised during the validation process
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages = []

    def new_error(self, msg):
        self.error_messages.append(msg)

    def raise_if_errors(self):
        if self.error_messages:
            raise self


def format_spreadsheet_rows_as_dict(rows_table, date, state):
    """
    Receives rows.Table object, a date and a brazilan UF, validates the data
    and returns a dict in the formatted data:

    This is an auxiliary method used by covid19.forms.StateSpreadsheetForm with the uploaded file
    """
    # TODO: https://github.com/turicas/brasil.io/issues/210
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
    for entry in rows_table:
        city = getattr(entry, city_attr, None)
        confirmed = getattr(entry, confirmed_attr, None)
        deaths = getattr(entry, deaths_attr, None)

        if not confirmed and deaths or not deaths and confirmed:
            validation_errors.new_error(f'Dados de casos ou óbitos incompletos na linha {city}')

        confirmed = confirmed or 0
        deaths = deaths or 0
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
        elif not has_total and result['city'] is None:
            has_total = True
        elif not has_undefined and result['city'] == UNDEFINED_DISPLAY:
            has_undefined = True
        results.append(result)

    if not has_total:
        validation_errors.new_error(f'A linha "{TOTAL_LINE_DISPLAY}" está faltando na planilha')
    if not has_undefined:
        validation_errors.new_error(f'A linha "{UNDEFINED_DISPLAY}" está faltando na planilha')

    validation_errors.raise_if_errors()
    return results


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

    return data


def _get_column_name(field_names, options):
    # XXX: this function expects all keys already in lowercase and slugified by `rows` library
    valid_columns = [key for key in field_names if key in options]
    if not valid_columns:
        raise ValueError(f"A coluna '{options[0]}' não existe")
    elif len(valid_columns) > 1:
        raise ValueError(f"Foi encontrada mais de uma coluna possível para '{options[0]}'")
    return valid_columns[0]
