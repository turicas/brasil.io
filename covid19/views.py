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
from covid19.models import StateSpreadsheet

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
    if state:
        state = state.upper()

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
        state = state.upper()
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


def make_aggregate(
    reports,
    confirmed,
    deaths,
    affected_cities,
    cities,
    affected_population,
    population,
    cities_with_deaths,
    for_state=False,
):
    data = [
        {
            "title": "Boletins coletados",
            "value": reports,
            "tooltip": "Total de boletins epidemiológicos coletados pelos voluntários",
        },
        {
            "title": "Casos confirmados",
            "value": confirmed,
            "tooltip": "Total de casos confirmados",
        },
        {
            "decimal_places": 2,
            "title": "Óbitos confirmados",
            "tooltip": "Total de óbitos confirmados",
            "value": deaths,
            "value_percent": 100 * (deaths / confirmed),
        },
        {
            "decimal_places": 0,
            "title": "Municípios atingidos",
            "tooltip": "Total de municípios com casos confirmados",
            "value": affected_cities,
            "value_percent": 100 * (affected_cities / cities),
        },
        {
            "decimal_places": 0,
            "title": "População desses municípios",
            "tooltip": "População dos municípios com casos confirmados (segundo estimativa IBGE 2019)",
            "value": f"{affected_population / 1_000_000:.0f}M",
            "value_percent": 100 * (affected_population / population),
        },
        {
            "decimal_places": 0,
            "title": "Municípios c/ óbitos",
            "tooltip": "Total de municípios com óbitos confirmados (o percentual é em relação ao total de municípios com casos confirmados)",
            "value": cities_with_deaths,
            "value_percent": 100 * (cities_with_deaths / affected_cities),
        },
    ]
    if for_state:
        for row in data:
            row["tooltip"] += " nesse estado"
    return data


def dashboard(request, state=None):
    if state is not None and not get_state_info(state):
        raise Http404
    if state:
        state = state.upper()

    country_aggregate = make_aggregate(
        reports=stats.total_reports,
        confirmed=stats.total_confirmed,
        deaths=stats.total_deaths,
        affected_cities=stats.affected_cities,
        cities=stats.number_of_cities,
        affected_population=stats.affected_population,
        population=stats.total_population,
        cities_with_deaths=stats.cities_with_deaths,
    )
    if state:
        city_data = stats.city_data_for_state(state)
        state_data = STATE_BY_ACRONYM[state]
        state_id = state_data.ibge_code
        state_name = state_data.name
        state_aggregate = make_aggregate(
            reports=stats.total_reports_for_state(state),
            confirmed=stats.total_confirmed_for_state(state),
            deaths=stats.total_deaths_for_state(state),
            affected_cities=stats.affected_cities_for_state(state),
            cities=stats.number_of_cities_for_state(state),
            affected_population=stats.affected_population_for_state(state),
            population=stats.total_population_for_state(state),
            cities_with_deaths=stats.cities_with_deaths_for_state(state),
            for_state=True
        )
    else:
        city_data = stats.city_data
        state_id = state_name = None
        state_aggregate = None

    return render(
        request,
        "dashboard.html",
        {
            "country_aggregate": country_aggregate,
            "state_aggregate": state_aggregate,
            "city_data": city_data,
            "state": state,
            "state_id": state_id,
            "state_name": state_name,
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
        response[
            "Content-Type"
        ] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        response["Content-Disposition"] = f"attachment; filename={state}.xlsx"
        return response
    except SpreadsheetValidationErrors as e:
        return JsonResponse({"errors": e.error_messages}, status=400)


@disable_non_logged_user_cache
def status(request):
    data = []
    for state in STATES:
        uf = state.acronym
        qs = StateSpreadsheet.objects.from_state(uf).order_by('-date')
        table_entry = {
            'uf': uf,
            'state': state.name,
            'status': '',
            'report_date': None,
            'report_date_str': '',
            'spreadsheet': None,
        }

        most_recet = qs.first()
        if most_recet:
            table_entry['spreadsheet'] = most_recet
            table_entry['status'] = most_recet.get_status_display()
            table_entry['report_date'] = most_recet.date
            table_entry['report_date_str'] = str(most_recet.date)

        data.append(table_entry)

    return render(request, "covid-status.html", {'import_data': data})
