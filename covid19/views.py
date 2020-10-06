import datetime
import random

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from brazil_data.cities import get_state_info
from brazil_data.states import STATE_BY_ACRONYM, STATES
from brazil_data.util import row_to_column
from core.middlewares import disable_non_logged_user_cache
from core.util import cached_http_get_json
from covid19.epiweek import get_epiweek
from covid19.exceptions import SpreadsheetValidationErrors
from covid19.geo import city_geojson, state_geojson
from covid19.models import DailyBulletin, StateSpreadsheet
from covid19.newstats import BoletimStats, CasoStats, CityStats
from covid19.spreadsheet import merge_state_data
from covid19.stats import Covid19Stats, max_values

stats = Covid19Stats()


def volunteers(request):
    url = "https://data.brasil.io/meta/covid19-voluntarios.json"
    volunteers = cached_http_get_json(url, 5)
    random.shuffle(volunteers)
    return render(request, "covid19/volunteers.html", {"volunteers": volunteers})


def cities(request):
    state = request.GET.get("state", None)
    if state is not None and not get_state_info(state):
        raise Http404

    country_caso_stats = CasoStats()
    brazil_city_data = country_caso_stats.per_city
    if state:
        state_caso_stats = CasoStats(state)
        city_data = state_caso_stats.per_city
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
    return [row for index, row in enumerate(data) if index >= skip and row["epidemiological_week"] < until_epiweek]


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
        state_caso_stats = CasoStats(state)
        city_data = state_caso_stats.per_city
    else:
        high_fidelity = False
        country_caso_stats = CasoStats()
        city_data = country_caso_stats.per_city

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

    country_city_stats = CityStats()
    country_boletim_stats = BoletimStats()
    country_caso_stats = CasoStats()

    country_aggregate = make_aggregate(
        reports=country_boletim_stats.total_reports,
        affected_cities=country_caso_stats.number_of_cities_with_cases,
        cities_with_deaths=country_caso_stats.number_of_cities_with_deaths,
        cities=country_city_stats.number_of_cities,
        affected_population=country_caso_stats.affected_population,
        population=country_city_stats.population,
        confirmed=country_caso_stats.confirmed,
        deaths=country_caso_stats.deaths,
    )
    if state:
        state_city_stats = CityStats(state)
        state_boletim_stats = BoletimStats(state)
        state_caso_stats = CasoStats(state)

        city_data = state_caso_stats.per_city
        state_data = STATE_BY_ACRONYM[state]
        state_id = state_data.ibge_code
        state_name = state_data.name

        state_aggregate = make_aggregate(
            reports=state_boletim_stats.total_reports,
            affected_cities=state_caso_stats.number_of_cities_with_cases,
            cities_with_deaths=state_caso_stats.number_of_cities_with_deaths,
            cities=state_city_stats.number_of_cities,
            affected_population=state_caso_stats.affected_population,
            population=state_city_stats.population,
            confirmed=state_caso_stats.confirmed,
            deaths=state_caso_stats.deaths,
            for_state=True,
        )
    else:
        city_data = country_caso_stats.per_city
        state_id = state_name = None
        state_aggregate = None

    return render(
        request,
        "covid19/dashboard.html",
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
        data = merge_state_data(state)
        # Filter out empty reports and cases
        data["reports"] = [
            # Here we export the `report` again, including only the fields we
            # want (the old JSON can come with other columns).
            {"date": report["date"], "notes": report["notes"], "state": state_info.state, "url": report["url"],}
            for report in data["reports"]
            if any(report.values())
        ]
        data["cases"] = [
            case
            for case in data["cases"]
            if any(value for key, value in case.items() if key != "municipio" and value not in ("", None))
        ]
        return JsonResponse(data, safe=False)
    except SpreadsheetValidationErrors as e:
        return JsonResponse({"errors": e.error_messages}, status=400)


@disable_non_logged_user_cache
def status(request):
    data = []
    for state in STATES:
        uf = state.acronym
        qs = StateSpreadsheet.objects.deployable_for_state(uf, only_active=False)
        table_entry = {
            "uf": uf,
            "state": state.name,
            "status": "",
            "report_date": None,
            "report_date_str": "",
            "spreadsheet": None,
        }

        most_recent = qs.first()
        if most_recent:
            table_entry["spreadsheet"] = most_recent
            table_entry["status"] = most_recent.get_status_display()
            if most_recent.cancelled:
                table_entry["status"] += " (cancelada)"
            table_entry["report_date"] = most_recent.date
            table_entry["report_date_str"] = str(most_recent.date)
            state_totals = [item for item in most_recent.table_data if item["city"] is None][0]
            table_entry["total_confirmed"] = state_totals["confirmed"]
            table_entry["total_deaths"] = state_totals["deaths"]

        data.append(table_entry)

    def row_sort(row):
        date = row["report_date"] or datetime.date(1970, 1, 1)
        return (date, row["state"])

    data.sort(key=row_sort)
    return render(request, "covid19/status.html", {"import_data": data})


@disable_non_logged_user_cache
def list_bulletins(request):
    bulletins = DailyBulletin.objects.order_by("-date").filter(date__lte=timezone.now().date())
    return render(request, "covid19/bulletins.html", {"bulletins": bulletins})
