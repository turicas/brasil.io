import datetime
import json

from django.shortcuts import render
from django.utils.text import slugify

from covid19.stats import Covid19Stats


def dashboard(request):
    stats = Covid19Stats()
    affected_cities = stats.affected_cities
    affected_population = stats.affected_population
    cities_with_deaths = stats.cities_with_deaths
    total_confirmed = stats.total_confirmed
    total_deaths = stats.total_deaths
    total_population = stats.total_population

    aggregate = [
        {
            "title": "Boletins coletados",
            "value": stats.total_reports,
            "tooltip": "Total de boletins das Secretarias Estaduais de Saúde coletados pelos voluntários",
        },
        {
            "title": "Casos confirmados",
            "value": total_confirmed,
            "tooltip": "Total de casos confirmados",
        },
        {
            "title": "Óbitos confirmados",
            "value": total_deaths,
            "tooltip": "Total de óbitos confirmados",
        },
        {
            "title": "Municípios atingidos",
            "value": f"{affected_cities} ({100 * affected_cities / 5570:.0f}%)",
            "tooltip": "Total de municípios com casos confirmados",
        },
        {
            "title": "População desses municípios",
            "value": f"{affected_population / 1_000_000:.0f}M ({100 * (affected_population / total_population):.0f}%)",
            "tooltip": "População dos municípios com casos confirmados, segundo estimativa IBGE 2019",
        },
        {
            "title": "Municípios c/ óbitos",
            "value": f"{cities_with_deaths} ({100 * cities_with_deaths / affected_cities:.0f}%)",
            "tooltip": "Total de municípios com óbitos confirmados (o percentual é em relação ao total de municípios com casos confirmados)",
        },
    ]

    value_keys = ("confirmed", "deaths", "death_rate", "confirmed_per_100k_inhabitants")
    city_values = {key: {} for key in value_keys}
    city_data = []
    # TODO: what should we do about "Importados/Indefinidos"?
    for row in stats.city_cases.filter(city_ibge_code__isnull=False):
        row = row.__dict__
        for key in value_keys:
            row[key] = row[key] or 0
            city_values[key][row["city_ibge_code"]] = row[key]
        row["death_rate_percent"] = row.pop("death_rate") * 100
        row["date_str"] = str(row["date"])
        row["city_str"] = slugify(row["city"])
        year, month, day = row["date_str"].split("-")
        row["date"] = datetime.date(int(year), int(month), int(day))
        city_data.append(row)
    max_values = {key: max(city_values[key].values()) for key in value_keys}

    return render(
        request,
        "dashboard.html",
        {"city_data": city_data, "aggregate": aggregate, "city_values_json": json.dumps(city_values), "max_values_json": json.dumps(max_values)},
    )
