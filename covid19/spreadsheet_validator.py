from rows.fields import IntegerField

from django.forms import ValidationError

from brazil_data.cities import get_city_info, get_state_info


TOTAL_LINE_DISPLAY = 'TOTAL NO ESTADO'
UNDEFINED_DISPLAY = 'Importados/Indefinidos'
INVALID_CITY_CODE = -1


def format_spreadsheet_rows_as_dict(rows_table, date, state):
    """
    Receives rows.Table object, a date and a brazilan UF, validates the data
    and returns a dict in the formatted data:

    This is an auxiliary method used by covid19.forms.StateSpreadsheetForm with the uploaded file
    """
    # TODO: https://github.com/turicas/brasil.io/issues/210
    field_names = rows_table.field_names

    confirmed_attr = _get_column_name(
        field_names, ['confirmados', 'confirmado', 'casos_confirmados']
    )
    deaths_attr = _get_column_name(field_names, ['obitos', 'obito', 'morte', 'mortes'])
    city_attr = _get_column_name(field_names, ['municipio', 'cidade'])

    if not rows_table.fields[confirmed_attr] == IntegerField:
        raise ValidationError('A coluna "Confirmados" precisa ter somente números inteiros"')
    if not rows_table.fields[deaths_attr] == IntegerField:
        raise ValidationError('A coluna "Mortes" precisa ter somente números inteiros"')

    results = []
    bad_cities = []
    has_total, has_undefined = False, False
    for i, entry in enumerate(rows_table):
        city = getattr(entry, city_attr, None)
        confirmed = getattr(entry, confirmed_attr, None)
        deaths = getattr(entry, deaths_attr, None)

        if confirmed is None:
            raise ValidationError(f'Valor nulo para casos confirmados na linha {i + 1} da planilha')
        if deaths is None:
            raise ValidationError(f'Valor nulo para óbitos na linha {i + 1} da planilha')
        if deaths > confirmed:
            raise ValidationError(
                f'Valor de óbitos maior que casos confirmados na linha {i + 1} da planilha'
            )

        result = _parse_city_data(city, confirmed, deaths, date, state)
        if result['city_ibge_code'] == INVALID_CITY_CODE:
            bad_cities.append(city)
        elif not has_total and result['city'] == TOTAL_LINE_DISPLAY:
            has_total = True
        elif not has_undefined and result['city'] == UNDEFINED_DISPLAY:
            has_undefined = True
        results.append(result)

    if not has_total:
        raise ValidationError(f'A linha "{TOTAL_LINE_DISPLAY}" está faltando na planilha')
    if not has_undefined:
        raise ValidationError(f'A linha "{UNDEFINED_DISPLAY}" está faltando na planilha')
    if bad_cities:
        bad_cities = ', '.join(bad_cities)
        raise ValidationError(f'As seguintes cidades não pertencem a UF {state}: {bad_cities}')

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
        raise ValidationError(f"Column '{options[0]}' not found")
    elif len(valid_columns) > 1:
        raise ValidationError(f"Found more than one '{options[0]}' column")
    return valid_columns[0]
