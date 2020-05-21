import datetime
import random
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.db import transaction

from rest_framework import views
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response

from brazil_data.cities import get_state_info
from brazil_data.states import STATE_BY_ACRONYM, STATES
from core.middlewares import disable_non_logged_user_cache
from core.util import cached_http_get_json
from covid19.exceptions import SpreadsheetValidationErrors
from covid19.forms import StateSpreadsheetForm
from covid19.geo import city_geojson, state_geojson
from covid19.models import StateSpreadsheet
from covid19.spreadsheet import create_merged_state_spreadsheet
from covid19.stats import Covid19Stats, max_values
from covid19.util import row_to_column
from covid19.epiweek import get_epiweek
from covid19.models import StateSpreadsheet
from covid19.signals import new_spreadsheet_imported_signal

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


def clean_daily_data(data, skip=0, diff=-1):
    now = datetime.datetime.now()
    today = datetime.date(now.year, now.month, now.day)
    first_date = min(row["date"] for row in data).split("-")
    first_date = datetime.date(*[int(item) for item in first_date])
    until_date = str(today + datetime.timedelta(days=diff))
    from_date = str(first_date + datetime.timedelta(days=skip))
    return [row for row in data if from_date <= row["date"] <= until_date]


def clean_weekly_data(data, skip=0, diff_days=-14):
    now = datetime.datetime.now()
    today = datetime.date(now.year, now.month, now.day)
    _, until_epiweek = get_epiweek(today + datetime.timedelta(days=diff_days))
    return [
        row
        for index, row in enumerate(data)
        if index >= skip and row["epidemiological_week"] < until_epiweek
    ]


def historical_data(request, period):
    state = request.GET.get("state", None)
    if period not in ("daily", "weekly"):
        raise Http404
    elif state is not None and not get_state_info(state):
        raise Http404

    if period == "daily":
        from_states = stats.historical_case_data_for_state_per_day(state)
        from_registries = stats.historical_registry_data_for_state_per_day(state)
        from_registries_excess = stats.excess_deaths_registry_data_for_state_per_day(state)
    elif period == "weekly":
        from_states = stats.historical_case_data_for_state_per_epiweek(state)
        from_registries = stats.historical_registry_data_for_state_per_epiweek(state)
        from_registries_excess = stats.excess_deaths_registry_data_for_state_per_epiweek(state)

    # Remove last period since it won't be complete
    if period == "daily":
        from_states = clean_daily_data(from_states, skip=0, diff=-1)
        from_registries = clean_daily_data(from_registries, skip=7, diff=-14)
        from_registries_excess = clean_daily_data(from_registries_excess, skip=7, diff=-14)
    if period == "weekly":
        from_states = clean_weekly_data(from_states, diff_days=-7)
        from_registries = clean_weekly_data(from_registries, skip=1, diff_days=-14)
        from_registries_excess = clean_weekly_data(from_registries_excess, skip=1, diff_days=-14)

    state_data = row_to_column(from_states)
    registry_data = row_to_column(from_registries)
    registry_excess_data = row_to_column(from_registries_excess)
    data = {
        "from_states": state_data,
        "from_registries": registry_data,
        "from_registries_excess": registry_excess_data,
    }
    return JsonResponse(data)


def historical_daily(request):
    return historical_data(request, "daily")


def historical_weekly(request):
    return historical_data(request, "weekly")


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
            feature for feature in data["features"] if int(feature["properties"]["CD_GEOCUF"]) == state_id
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
    data["features"] = [feature for feature in data["features"] if feature["id"] in city_ids]
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
        {"title": "Casos confirmados", "value": confirmed, "tooltip": "Total de casos confirmados",},
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
            "tooltip": "Total de municípios com óbitos confirmados (o percentual é em relação ao total de municípios com casos confirmados)",  # noqa
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
        affected_cities=stats.number_of_affected_cities,
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
            affected_cities=stats.number_of_affected_cities_for_state(state),
            cities=stats.number_of_cities_for_state(state),
            affected_population=stats.affected_population_for_state(state),
            population=stats.total_population_for_state(state),
            cities_with_deaths=stats.cities_with_deaths_for_state(state),
            for_state=True,
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
            "city_slug": None,  # TODO: change
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
        response["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        response["Content-Disposition"] = f"attachment; filename={state}.xlsx"
        return response
    except SpreadsheetValidationErrors as e:
        return JsonResponse({"errors": e.error_messages}, status=400)


@disable_non_logged_user_cache
def status(request):
    data = []
    for state in STATES:
        uf = state.acronym
        qs = StateSpreadsheet.objects.from_state(uf).order_by("-date")
        table_entry = {
            "uf": uf,
            "state": state.name,
            "status": "",
            "report_date": None,
            "report_date_str": "",
            "deployed_date": None,
            "deployed_date_str": "",
            "spreadsheet": None,
        }

        most_recet = qs.first()
        if most_recet:
            table_entry["spreadsheet"] = most_recet
            table_entry["status"] = most_recet.get_status_display()
            table_entry["report_date"] = most_recet.date
            table_entry["report_date_str"] = str(most_recet.date)
            last_deployed = qs.deployed().first()
            if last_deployed:
                table_entry["deployed_date"] = last_deployed.date
                table_entry["deployed_date_str"] = str(last_deployed.date)

        data.append(table_entry)

    return render(request, "covid-status.html", {"import_data": data})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def state_spreadsheet_view_list(request, *args, **kwargs):

    def gen_file(name, content):
        if isinstance(content, str):
            content = str.encode(content)
        return SimpleUploadedFile(name, content)

    if request.method == 'POST':
        data = json.loads(request.body)

        data["state"] = kwargs['state']  # sempre terá um state dado que ele está na URL

        state = data['state']
        date = data['date']
        filename = f"{state}-{date}-import.csv"

        file_data = {"file": gen_file(filename, ''.join(data['file']))}

        form = StateSpreadsheetForm(data, file_data, user=request.user)

        if form.is_valid():
            transaction.on_commit(
                lambda: new_spreadsheet_imported_signal.send(
                    sender=self,
                    spreadsheet=spreadsheet
                )
            )

            spreadsheet = form.save()
            spreadsheet.refresh_from_db()

            return JsonResponse({"warnings": spreadsheet.warnings, "detail_url": spreadsheet.admin_url})

        return JsonResponse({'errors': form.errors}, status=400)
