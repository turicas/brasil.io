def format_spreadsheet_rows_as_dict(rows):
    """
    Receives rows as a rows.Table object and return a dict in the following format:

    {
    'total': {'confirmados': 100, 'mortes': 30},
    'importados_indefinidos': {'confirmados': 2, 'mortes': 1},
    'cidades': {
        'Cidade1': {'confirmados': 9, 'mortes': 1},
        'Cidade2': {'confirmados': 11, 'mortes': 2},
        ...
    }

    This is an auxiliary method used by covid19.forms.StateSpreadsheetForm with the uploaded file
    """
    # TODO: https://github.com/turicas/brasil.io/issues/209
    # TODO: https://github.com/turicas/brasil.io/issues/210
    result = {
        'total': {},
        'importados_indefinidos': {},
        'cidades': {},
    }

    for entry in rows:
        city, confirmed, deaths = entry.municipio, entry.confirmados, entry.mortes
        data = {'confirmados': confirmed, 'mortes': deaths}

        if city == 'TOTAL NO ESTADO':
            result['total'] = data
        elif city == 'Importados/Indefinidos':
            result['importados_indefinidos'] = data
        else:
            result['cidades'][city] = data

    return result
