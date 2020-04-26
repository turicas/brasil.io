import random

from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render

from brazil_data.cities import get_state_info
from brazil_data.states import STATES, STATE_BY_ACRONYM
from core.middlewares import disable_non_logged_user_cache
from core.util import cached_http_get_json
from covid19.exceptions import SpreadsheetValidationErrors
from covid19.geo import city_geojson, state_geojson
from covid19.spreadsheet import create_merged_state_spreadsheet
from covid19.stats import Covid19Stats, max_values

stats = Covid19Stats()


def volunteers(request):
    url = "https://data.brasil.io/meta/covid19-voluntarios.json"
    volunteers = cached_http_get_json(url, 5)
    random.shuffle(volunteers)
    return render(request, "volunteers.html", {"volunteers": volunteers})


def cities(request):
    state = request.GET.get("state", None)
    if state is not None and not get_state_info(state):
        raise Http404

    brazil_city_data = stats.city_data
    if state:
        city_data = stats.city_data_for_state(state)
        total_row = stats.state_row(state)
    else:
        city_data = brazil_city_data
        total_row = stats.country_row

    result = {
        "cities": {row["city_ibge_code"]: row for row in city_data},
        "max": max_values(brazil_city_data),
        "total": total_row,
    }
    return JsonResponse(result)


def states_geojson(request):
    state = request.GET.get("state", None)
    if state is not None and not get_state_info(state):
        raise Http404

    data = state_geojson(high_fidelity=bool(state))
    if state:
        state_id = STATE_BY_ACRONYM[state].ibge_code
        data["features"] = [
            feature
            for feature in data["features"]
            if int(feature["properties"]["CD_GEOCUF"]) == state_id
        ]
    return JsonResponse(data, content_type="application/geo+json")


def cities_geojson(request):
    state = request.GET.get("state", None)
    if state is not None and not get_state_info(state):
        raise Http404
    elif state:
        high_fidelity = True
        city_data = stats.city_data_for_state(state)
    else:
        high_fidelity = False
        city_data = stats.city_data

    city_ids = set(row["city_ibge_code"] for row in city_data)
    data = city_geojson(high_fidelity=high_fidelity)
    data["features"] = [
        feature for feature in data["features"] if feature["id"] in city_ids
    ]
    return JsonResponse(data, content_type="application/geo+json")


def dashboard(request, state=None):
    if state is not None and not get_state_info(state):
        raise Http404
    elif state:
        state_id = STATE_BY_ACRONYM[state].ibge_code
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
    if state:
        city_data = stats.city_data_for_state(state)
    else:
        city_data = stats.city_data

    return render(
        request,
        "dashboard.html",
        {
            "aggregate": aggregate,
            "city_data": city_data,
            "state": state,
            "state_id": state_id,
            "states": STATES,
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
