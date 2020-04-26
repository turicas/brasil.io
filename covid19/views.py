import random

from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render

from brazil_data.cities import get_state_info
from core.middlewares import disable_non_logged_user_cache
from core.util import cached_http_get_json
from covid19.exceptions import SpreadsheetValidationErrors
from covid19.geo import city_geojson
from covid19.spreadsheet import create_merged_state_spreadsheet
from covid19.stats import Covid19Stats

stats = Covid19Stats()
state_codes = {
    "AC": 12, "AL": 27, "AM": 13, "AP": 16, "BA": 29, "CE": 23, "DF": 53,
    "ES": 32, "GO": 52, "MA": 21, "MG": 31, "MS": 50, "MT": 51, "PA": 15,
    "PB": 25, "PE": 26, "PI": 22, "PR": 41, "RJ": 33, "RN": 24, "RO": 11,
    "RR": 14, "RS": 43, "SC": 42, "SE": 28, "SP": 35, "TO": 17,
}


def volunteers(request):
    url = "https://data.brasil.io/meta/covid19-voluntarios.json"
    volunteers = cached_http_get_json(url, 5)
    random.shuffle(volunteers)
    return render(request, "volunteers.html", {"volunteers": volunteers})


def cities(request):
    state = request.GET.get("state", None)
    if state is not None and not get_state_info(state):
        raise Http404
    city_data = stats.city_data
    if state:
        city_data["cities"] = {
            key: value
            for key, value in city_data["cities"].items()
            if value["state"] == state
        }
    return JsonResponse(city_data)


def cities_geojson(request):
    state = request.GET.get("state", None)
    if state is not None and not get_state_info(state):
        raise Http404
    elif state:
        high_fidelity = True
        city_ids = set(
            key
            for key, value in stats.city_data["cities"].items()
            if value["state"] == state
        )
    else:
        high_fidelity = False
        city_ids = set(stats.city_data["cities"].keys())
    data = city_geojson(high_fidelity=high_fidelity)
    data["features"] = [
        feature for feature in data["features"] if feature["id"] in city_ids
    ]
    # TODO: return GeoJSONResponse
    return JsonResponse(data)


def dashboard(request, state=None):
    if state is not None and not get_state_info(state):
        raise Http404
    elif state:
        state_id = state_codes[state]
    else:
        state_id = None

    aggregate = [
        {
            "title": "Boletins coletados",
            "value": stats.total_reports,
            "tooltip": "Total de boletins das Secretarias Estaduais de Saúde coletados pelos voluntários",
        },
        {
            "title": "Casos confirmados",
            "value": stats.total_confirmed,
            "tooltip": "Total de casos confirmados",
        },
        {
            "decimal_places": 2,
            "title": "Óbitos confirmados",
            "tooltip": "Total de óbitos confirmados",
            "value": stats.total_deaths,
            "value_percent": 100 * (stats.total_deaths / stats.total_confirmed),
        },
        {
            "decimal_places": 0,
            "title": "Municípios atingidos",
            "tooltip": "Total de municípios com casos confirmados",
            "value": stats.affected_cities,
            "value_percent": 100 * (stats.affected_cities / 5570),
        },
        {
            "decimal_places": 0,
            "title": "População desses municípios",
            "tooltip": "População dos municípios com casos confirmados, segundo estimativa IBGE 2019",
            "value": f"{stats.affected_population / 1_000_000:.0f}M",
            "value_percent": 100 * (stats.affected_population / stats.total_population),
        },
        {
            "decimal_places": 0,
            "title": "Municípios c/ óbitos",
            "tooltip": "Total de municípios com óbitos confirmados (o percentual é em relação ao total de municípios com casos confirmados)",
            "value": stats.cities_with_deaths,
            "value_percent": 100 * (stats.cities_with_deaths / stats.affected_cities),
        },
    ]
    city_data = stats.city_data
    if state:
        # TODO: implement "stats.city_data_for_state"
        city_data["cities"] = {
            key: value
            for key, value in city_data["cities"].items()
            if value["state"] == state
        }

    return render(
        request,
        "dashboard.html",
        {
            "aggregate": aggregate,
            "city_data": city_data["cities"].values(),
            "state": state,
            "state_id": state_id,
        },
    )


@disable_non_logged_user_cache
def import_spreadsheet_proxy(request, state):
    state_info = get_state_info(state)
    if not state_info:
        raise Http404

    try:
        content = create_merged_state_spreadsheet(state)
        response = HttpResponse(content)
        response['Content-Type'] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        response['Content-Disposition'] = f"attachment; filename={state}.xlsx"
        return response
    except SpreadsheetValidationErrors as e:
        return JsonResponse({'errors': e.error_messages}, status=400)
