import rows

from brazil_data.cities import brazilian_cities_per_state


def create_template(state):
    state_cities = brazilian_cities_per_state()[state]
    result = [
        {"municipio": "TOTAL NO ESTADO", "confirmados": None, "mortes": None},
        {"municipio": "Importados/Indefinidos", "confirmados": None, "mortes": None},
    ]
    for city in state_cities:
        result.append({"municipio": city, "confirmados": None, "mortes": None})
    return rows.import_from_dicts(result)


def run():
    """
    Run with:

    $ python manage.py runscript brazilian_cities
    """
    cities = brazilian_cities_per_state()
    for state, state_cities in cities.items():
        print(f"===== {state} =====")
        for city in state_cities:
            print(f"  {city}")
        print()

    # To create/save templates:
    # rows.export_to_csv(create_template("PR"), "casos-PR.csv")
    # rows.export_to_xls(create_template("PR"), "casos-PR.xls")
    # rows.export_to_xlsx(create_template("PR"), "casos-PR.xlsx")
