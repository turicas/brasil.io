from django.http import JsonResponse
from django.shortcuts import render

from .geo import city_geojson
from .stats import Covid19Stats


stats = Covid19Stats()

def cities(request):
    city_data = stats.city_data
    return JsonResponse(city_data)


def cities_geojson(request):
    city_ids = set(int(item) for item in stats.city_data["cities"].keys())
    data = city_geojson()
    data["features"] = [
        feature
        for feature in data["features"]
        if feature["id"] in city_ids
    ]
    # TODO: return GeoJSONResponse
    return JsonResponse(data)


def dashboard(request):
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
    city_data = stats.city_data

    return render(
        request,
        "dashboard.html",
        {
            "city_data": city_data["cities"].values(),
            "aggregate": aggregate,
        },
    )
