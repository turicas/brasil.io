import random


CITIES_PREPOSITION = {
    "rio de janeiro": "no",
    "recife": "no",
    "brasil": "no",
}


CAPITALS = {
    "rio branco": "AC",
    "maceió": "AL",
    "macapá": "AP",
    "manaus": "AM",
    "salvador": "BA",
    "fortaleza": "CE",
    "vitória": "ES",
    "goiânia": "GO",
    "são luís": "MA",
    "cuiabá": "MT",
    "campo grande": "MS",
    "belo horizonte": "MG",
    "belém": "PA",
    "joão pessoa": "PB",
    "curitiba": "PR",
    "recife": "PE",
    "teresina": "PI",
    "rio de janeiro": "RJ",
    "natal": "RN",
    "porto alegre": "RS",
    "porto velho": "RO",
    "boa vista": "RR",
    "florianópolis": "SC",
    "são paulo": "SP",
    "aracaju": "SE",
    "palmas": "TO",
}


def format_city_name(name):
    return " ".join(n.capitalize() if len(n) > 2 else n for n in name.split())


def create_search_suggestions(cargos=None, cities=None):
    cargos = cargos or ("vereador", "prefeito",)
    cities = cities or list(CAPITALS.keys())

    suggestions = []
    url_prefix = "/eleicoes/2024/"
    for cargo in cargos:
        for city in cities:
            city_preposition = CITIES_PREPOSITION.get(city.lower(), "em")
            formatted_city = format_city_name(city)
            state_capital = CAPITALS.get(city.lower())
            title = f"{cargo.capitalize()} {city_preposition} {formatted_city}"
            path = f"{url_prefix}?cargo={cargo.capitalize()}"

            if state_capital is not None:
                title += f" ({state_capital})"
                path += f"&q={formatted_city}-{state_capital}"

            suggestions.append({"label": title, "path": path})

    random.shuffle(suggestions)
    return suggestions
