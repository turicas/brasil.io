import random

from django.http import JsonResponse
from django.shortcuts import render

from .geo import city_geojson
from .stats import Covid19Stats

from core.util import cached_http_get_json

stats = Covid19Stats()


def volunteers(request):
    url = "https://data.brasil.io/meta/covid19-voluntarios.json"
    volunteers = cached_http_get_json(url, 5)
    random.shuffle(volunteers)
    return render(request, "volunteers.html", {"volunteers": volunteers})


def cities(request):
    city_data = stats.city_data
    return JsonResponse(city_data)


def cities_geojson(request):
    city_ids = set(stats.city_data["cities"].keys())
    data = city_geojson()
    data["features"] = [
        feature for feature in data["features"] if feature["id"] in city_ids
    ]
    # TODO: return GeoJSONResponse
    return JsonResponse(data)


def br_int_format(number):
    return f"{number:,}".replace(",", ".")


def br_percent_format(a, b, decimal_places=2):
    value = 100 * (a / b)
    format_str = f"{{:.{decimal_places}f}}"
    return format_str.format(value).replace(".", ",") + "%"


def dashboard(request):
    affected_cities = stats.affected_cities
    affected_population = stats.affected_population
    cities_with_deaths = stats.cities_with_deaths
    total_confirmed = stats.total_confirmed
    total_deaths = stats.total_deaths
    total_population = stats.total_population

    affected_cities_str = br_int_format(affected_cities)
    affected_cities_percent_str = br_percent_format(affected_cities, 5570, 0)
    affected_population_str = f"{affected_population / 1_000_000:.0f}M"
    affected_population_percent_str = br_percent_format(
        affected_population, total_population, 0
    )
    cities_with_deaths_str = br_int_format(cities_with_deaths)
    cities_with_deaths_percent_str = br_percent_format(
        cities_with_deaths, affected_cities, 0
    )
    total_confirmed_str = br_int_format(total_confirmed)
    total_deaths_str = br_int_format(total_deaths)
    total_deaths_percent_str = br_percent_format(total_deaths, total_confirmed, 2)
    total_reports_str = br_int_format(stats.total_reports)

    aggregate = [
        {
            "title": "Boletins coletados",
            "value": total_reports_str,
            "tooltip": "Total de boletins das Secretarias Estaduais de Saúde coletados pelos voluntários",
        },
        {
            "title": "Casos confirmados",
            "value": total_confirmed_str,
            "tooltip": "Total de casos confirmados",
        },
        {
            "title": "Óbitos confirmados",
            "value": f"{total_deaths_str} ({total_deaths_percent_str})",
            "tooltip": "Total de óbitos confirmados",
        },
        {
            "title": "Municípios atingidos",
            "value": f"{affected_cities_str} ({affected_cities_percent_str})",
            "tooltip": "Total de municípios com casos confirmados",
        },
        {
            "title": "População desses municípios",
            "value": f"{affected_population_str} ({affected_population_percent_str})",
            "tooltip": "População dos municípios com casos confirmados, segundo estimativa IBGE 2019",
        },
        {
            "title": "Municípios c/ óbitos",
            "value": f"{cities_with_deaths_str} ({cities_with_deaths_percent_str})",
            "tooltip": "Total de municípios com óbitos confirmados (o percentual é em relação ao total de municípios com casos confirmados)",
        },
    ]
    city_data = stats.city_data

    return render(
        request,
        "dashboard.html",
        {"city_data": city_data["cities"].values(), "aggregate": aggregate},
    )
