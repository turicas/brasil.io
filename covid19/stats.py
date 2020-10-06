from collections import Counter
from itertools import groupby

from django.db.models import Max, Sum

from core.models import get_table_model


def max_values(data):
    desired_keys = (
        "confirmed",
        "confirmed_per_100k_inhabitants",
        "deaths",
        "death_rate_percent",
        "deaths_per_100k_inhabitants",
    )
    return {key: max(row[key] for row in data) for key in desired_keys}


def group_deaths(data):
    key_map = {
        "deathgroup_other": ("deaths_septicemia", "deaths_indeterminate", "deaths_others",),
        "deathgroup_other_respiratory": ("deaths_pneumonia", "deaths_respiratory_failure", "deaths_sars",),
        "deathgroup_covid19": ("deaths_covid19",),
    }
    result = []
    for row in data:
        new = {
            "excess_deaths": (row.get("deaths_total") or 0) - (row.get("deaths_total_2019") or 0),
            "new_excess_deaths": (row.get("new_deaths_total") or 0) - (row.get("new_deaths_total_2019") or 0),
        }
        if "date" in row:
            new["date"] = row["date"]
        elif "epidemiological_week" in row:
            new["epidemiological_week"] = row["epidemiological_week"]
        for new_key, sum_keys in key_map.items():
            new[f"{new_key}_2020"] = sum(row.get(key) or 0 for key in sum_keys)
            new[f"new_{new_key}_2020"] = sum(row.get(f"new_{key}") or 0 for key in sum_keys)
            new[f"{new_key}_2019"] = sum(row.get(f"{key}_2019") or 0 for key in sum_keys)
            new[f"new_{new_key}_2019"] = sum(row.get(f"new_{key}_2019") or 0 for key in sum_keys)
        result.append(new)
    return result


class Covid19Stats:
    graph_daily_cases_columns = {
        "confirmed": (Sum, "last_available_confirmed"),
        "deaths": (Sum, "last_available_deaths"),
        "new_confirmed": (Sum, "new_confirmed"),
        "new_deaths": (Sum, "new_deaths"),
    }
    graph_weekly_cases_columns = {
        "confirmed": (Max, "last_available_confirmed"),
        "deaths": (Max, "last_available_deaths"),
        "new_confirmed": (Sum, "new_confirmed"),
        "new_deaths": (Sum, "new_deaths"),
    }
    graph_daily_registry_deaths_columns = {
        "deaths_covid19": (Sum, "deaths_covid19"),
        "deaths_indeterminate": (Sum, "deaths_indeterminate_2020"),
        "deaths_others": (Sum, "deaths_others_2020"),
        "deaths_pneumonia": (Sum, "deaths_pneumonia_2020"),
        "deaths_respiratory_failure": (Sum, "deaths_respiratory_failure_2020"),
        "deaths_sars": (Sum, "deaths_sars_2020"),
        "deaths_septicemia": (Sum, "deaths_septicemia_2020"),
        "deaths_total": (Sum, "deaths_total_2020"),
        "new_deaths_covid19": (Sum, "new_deaths_covid19"),
        "new_deaths_indeterminate": (Sum, "new_deaths_indeterminate_2020"),
        "new_deaths_others": (Sum, "new_deaths_others_2020"),
        "new_deaths_pneumonia": (Sum, "new_deaths_pneumonia_2020"),
        "new_deaths_respiratory_failure": (Sum, "new_deaths_respiratory_failure_2020"),
        "new_deaths_sars": (Sum, "new_deaths_sars_2020"),
        "new_deaths_septicemia": (Sum, "new_deaths_septicemia_2020"),
        "new_deaths_total": (Sum, "new_deaths_total_2020"),
        "deaths_indeterminate_2019": (Sum, "deaths_indeterminate_2019"),
        "deaths_others_2019": (Sum, "deaths_others_2019"),
        "deaths_pneumonia_2019": (Sum, "deaths_pneumonia_2019"),
        "deaths_respiratory_failure_2019": (Sum, "deaths_respiratory_failure_2019"),
        "deaths_sars_2019": (Sum, "deaths_sars_2019"),
        "deaths_septicemia_2019": (Sum, "deaths_septicemia_2019"),
        "deaths_total_2019": (Sum, "deaths_total_2019"),
        "new_deaths_indeterminate_2019": (Sum, "new_deaths_indeterminate_2019"),
        "new_deaths_others_2019": (Sum, "new_deaths_others_2019"),
        "new_deaths_pneumonia_2019": (Sum, "new_deaths_pneumonia_2019"),
        "new_deaths_respiratory_failure_2019": (Sum, "new_deaths_respiratory_failure_2019"),
        "new_deaths_sars_2019": (Sum, "new_deaths_sars_2019"),
        "new_deaths_septicemia_2019": (Sum, "new_deaths_septicemia_2019"),
        "new_deaths_total_2019": (Sum, "new_deaths_total_2019"),
    }
    graph_weekly_registry_deaths_columns = {
        "deaths_covid19": (Max, "deaths_covid19"),
        "deaths_indeterminate": (Max, "deaths_indeterminate_2020"),
        "deaths_others": (Max, "deaths_others_2020"),
        "deaths_pneumonia": (Max, "deaths_pneumonia_2020"),
        "deaths_respiratory_failure": (Max, "deaths_respiratory_failure_2020"),
        "deaths_sars": (Max, "deaths_sars_2020"),
        "deaths_septicemia": (Max, "deaths_septicemia_2020"),
        "deaths_total": (Max, "deaths_total_2020"),
        "new_deaths_covid19": (Sum, "new_deaths_covid19"),
        "new_deaths_indeterminate": (Sum, "new_deaths_indeterminate_2020"),
        "new_deaths_others": (Sum, "new_deaths_others_2020"),
        "new_deaths_pneumonia": (Sum, "new_deaths_pneumonia_2020"),
        "new_deaths_respiratory_failure": (Sum, "new_deaths_respiratory_failure_2020"),
        "new_deaths_sars": (Sum, "new_deaths_sars_2020"),
        "new_deaths_septicemia": (Sum, "new_deaths_septicemia_2020"),
        "new_deaths_total": (Sum, "new_deaths_total_2020"),
    }
    graph_weekly_registry_deaths_2019_columns = {
        "deaths_covid19": (Max, "deaths_covid19"),
        "deaths_indeterminate": (Max, "deaths_indeterminate_2019"),
        "deaths_others": (Max, "deaths_others_2019"),
        "deaths_pneumonia": (Max, "deaths_pneumonia_2019"),
        "deaths_respiratory_failure": (Max, "deaths_respiratory_failure_2019"),
        "deaths_sars": (Max, "deaths_sars_2019"),
        "deaths_septicemia": (Max, "deaths_septicemia_2019"),
        "deaths_total": (Max, "deaths_total_2019"),
        "new_deaths_covid19": (Sum, "new_deaths_covid19"),
        "new_deaths_indeterminate": (Sum, "new_deaths_indeterminate_2019"),
        "new_deaths_others": (Sum, "new_deaths_others_2019"),
        "new_deaths_pneumonia": (Sum, "new_deaths_pneumonia_2019"),
        "new_deaths_respiratory_failure": (Sum, "new_deaths_respiratory_failure_2019"),
        "new_deaths_sars": (Sum, "new_deaths_sars_2019"),
        "new_deaths_septicemia": (Sum, "new_deaths_septicemia_2019"),
        "new_deaths_total": (Sum, "new_deaths_total_2019"),
    }

    @property
    def Caso(self):
        return get_table_model("covid19", "caso")

    @property
    def CasoFull(self):
        return get_table_model("covid19", "caso_full")

    @property
    def ObitoCartorio(self):
        return get_table_model("covid19", "obito_cartorio")

    @property
    def state_cases(self):
        return self.Caso.objects.filter(is_last=True, place_type="state")

    @property
    def country_row(self):
        state_totals = self.state_totals
        confirmed = state_totals["total_confirmed"]
        deaths = state_totals["total_deaths"]
        population = state_totals["total_population"]
        # TODO: use new schema from caso_full when its ready
        # TODO: is there any way to move this to serializer?
        return {
            "city": "BR",
            "city_ibge_code": 0,
            "city_str": "BR",
            "confirmed": confirmed,
            "confirmed_per_100k_inhabitants": 100_000 * (confirmed / population),
            "date": state_totals["last_date"],
            "date_str": str(state_totals["last_date"]),
            "death_rate_percent": 100 * (deaths / confirmed),
            "deaths": deaths,
            "deaths_per_100k_inhabitants": 100_000 * (deaths / population),
            "estimated_population_2019": population,
            "state": "BR",
        }

    def state_row(self, state):
        cases_for_state = [case for case in self.state_cases if case.state == state]
        assert len(cases_for_state) == 1
        case = cases_for_state[0]

        confirmed = case.confirmed
        deaths = case.deaths
        population = case.estimated_population_2019
        state_name = case.state

        # TODO: use new schema from caso_full when its ready
        # TODO: is there any way to move this to serializer?
        return {
            "city": state_name,
            "city_ibge_code": case.city_ibge_code,
            "city_str": state_name,
            "confirmed": confirmed,
            "confirmed_per_100k_inhabitants": 100_000 * (confirmed / population),
            "date": case.date,
            "date_str": str(case.date),
            "death_rate_percent": 100 * (deaths / confirmed),
            "deaths": deaths,
            "deaths_per_100k_inhabitants": 100_000 * (deaths / population),
            "estimated_population_2019": population,
            "state": state,
        }

    @property
    def state_totals(self):
        return self.state_cases.aggregate(
            total_confirmed=Sum("confirmed"),
            total_deaths=Sum("deaths"),
            total_population=Sum("estimated_population_2019"),
            last_date=Max("date"),
        )

    def aggregate_state_data(self, select_columns, groupby_columns, state=None):
        qs = self.CasoFull.objects.filter(place_type="state")
        if state is not None:
            qs = qs.filter(state=state)
        annotate_dict = {alias: Function(column) for alias, (Function, column) in select_columns.items()}
        return list(qs.order_by(*groupby_columns).values(*groupby_columns).annotate(**annotate_dict))

    def aggregate_epiweek(self, data, group_key="epidemiological_week"):
        row_key = lambda row: row[group_key]  # noqa
        result = []
        data.sort(key=row_key)
        for epiweek, group in groupby(data, key=row_key):
            epidata = Counter()
            for row in group:
                for key in row:
                    if key in (group_key, "state"):
                        continue
                    epidata[key] += row[key] or 0
            result.append({group_key: epiweek, **epidata})
        return result

    def historical_case_data_for_state_per_day(self, state):
        return self.aggregate_state_data(
            groupby_columns=["date"], select_columns=self.graph_daily_cases_columns, state=state
        )

    def historical_case_data_for_state_per_epiweek(self, state):
        return self.aggregate_epiweek(
            self.aggregate_state_data(
                groupby_columns=["epidemiological_week", "state"],
                select_columns=self.graph_weekly_cases_columns,
                state=state,
            )
        )

    def aggregate_registry_data(self, select_columns, groupby_columns, state=None):
        qs = self.ObitoCartorio.objects
        if state is not None:
            qs = qs.filter(state=state)
        annotate_dict = {alias: Function(column) for alias, (Function, column) in select_columns.items()}
        return list(qs.order_by(*groupby_columns).values(*groupby_columns).annotate(**annotate_dict))

    def historical_registry_data_for_state_per_day(self, state=None):
        # If state = None, return data for Brazil
        return self.aggregate_registry_data(
            groupby_columns=["date"], select_columns=self.graph_daily_registry_deaths_columns, state=state
        )

    def excess_deaths_registry_data_for_state_per_day(self, state=None):
        data = self.historical_registry_data_for_state_per_day(state=state)
        return group_deaths(data)

    def historical_registry_data_for_state_per_epiweek(self, state=None):
        # If state = None, return data for Brazil
        data_2020 = self.aggregate_epiweek(
            self.aggregate_registry_data(
                groupby_columns=["epidemiological_week_2020", "state"],
                select_columns=self.graph_weekly_registry_deaths_columns,
                state=state,
            ),
            group_key="epidemiological_week_2020",
        )
        data_2020 = {row["epidemiological_week_2020"]: row for row in data_2020}
        data_2019 = self.aggregate_epiweek(
            self.aggregate_registry_data(
                groupby_columns=["epidemiological_week_2019", "state"],
                select_columns=self.graph_weekly_registry_deaths_2019_columns,
                state=state,
            ),
            group_key="epidemiological_week_2019",
        )
        data_2019 = {row["epidemiological_week_2019"]: row for row in data_2019}
        epiweeks = sorted(set(data_2020.keys()) | set(data_2019.keys()))
        result = []
        for epiweek in epiweeks:
            new = {"epidemiological_week": epiweek}
            for key, value in data_2020.get(epiweek, {}).items():
                if key.startswith("epidemiological_week"):
                    continue
                new[key] = value
            for key, value in data_2019.get(epiweek, {}).items():
                if key.startswith("epidemiological_week") or "covid19" in key:
                    continue
                new[f"{key}_2019"] = value
            result.append(new)
        return result

    def excess_deaths_registry_data_for_state_per_epiweek(self, state=None):
        data = self.historical_registry_data_for_state_per_epiweek(state=state)
        return group_deaths(data)
