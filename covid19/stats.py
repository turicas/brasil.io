from cached_property import cached_property
from itertools import groupby

from django.db.models import Max, Sum

from brazil_data.states import STATE_BY_ACRONYM
from core.models import get_table_model
from covid19.serializers import CityCaseSerializer


class Covid19Stats:

    @cached_property
    def Boletim(self):
        return get_table_model("covid19", "boletim")

    @cached_property
    def Caso(self):
        return get_table_model("covid19", "caso")

    @cached_property
    def city_cases(self):
        return self.Caso.objects.filter(is_last=True, place_type="city")

    @cached_property
    def state_cases(self):
        return self.Caso.objects.filter(is_last=True, place_type="state")

    @property
    def total_reports(self):
        return self.Boletim.objects.count()

    @property
    def affected_cities(self):
        return self.city_cases.count()

    @property
    def cities_with_deaths(self):
        return self.city_cases.filter(deaths__gt=0).count()

    @property
    def state_totals(self):
        return self.state_cases.aggregate(
            total_confirmed=Sum("confirmed"),
            total_deaths=Sum("deaths"),
            total_population=Sum("estimated_population_2019"),
            last_date=Max("date"),
        )

    @property
    def country_totals(self):
        state_totals = self.state_totals
        confirmed = state_totals["total_confirmed"]
        deaths = state_totals["total_deaths"]
        population = state_totals["total_population"]
        # TODO: is there any way to move this to serializer?
        return {
            "city": "Brasil",
            "city_ibge_code": 0,
            "city_str": "Brasil",
            "confirmed": confirmed,
            "confirmed_per_100k_inhabitants": 100_000 * (confirmed / population),
            "date": state_totals["last_date"],
            "date_str": state_totals["last_date"],
            "death_rate_percent": 100 * (deaths / confirmed),
            "deaths": deaths,
            "deaths_per_100k_inhabitants": 100 * (deaths / population),
            "estimated_population_2019": population,
            "state": "BR",
        }

    @property
    def total_confirmed(self):
        return self.state_totals["total_confirmed"]

    @property
    def total_deaths(self):
        return self.state_totals["total_deaths"]

    @property
    def total_population(self):
        return self.state_totals["total_population"]

    @property
    def city_totals(self):
        return self.city_cases.aggregate(
            max_confirmed=Max("confirmed"),
            max_confirmed_per_100k_inhabitants=Max("confirmed_per_100k_inhabitants"),
            max_death_rate=Max("death_rate"),
            max_deaths=Max("deaths"),
            total_population=Sum("estimated_population_2019")
        )

    @property
    def affected_population(self):
        return self.city_totals["total_population"]

    @property
    def city_data(self):
        # XXX: what should we do about "Importados/Indefinidos"?
        desired_keys = (
            "confirmed",
            "confirmed_per_100k_inhabitants",
            "deaths",
            "death_rate_percent",
            "deaths_per_100k_inhabitants",
        )
        city_cases = self.city_cases.filter(city_ibge_code__isnull=False)
        serializer = CityCaseSerializer(instance=city_cases, many=True)
        cities = {
            row["city_ibge_code"]: row
            for row in serializer.data
            if (row["confirmed"], row["deaths"]) != (0, 0)
        }
        max_values = {
            key: max(row[key] for row in cities.values())
            for key in desired_keys
        }
        return {"cities": cities, "max": max_values, "total": self.country_totals}

    def most_recent_city_entries_for_state(self, state, date):
        return self._get_latest_cases(state, date, "city")

    def most_recent_state_entry(self, state, date):
        return self._get_latest_cases(state, date, "state")

    def _get_latest_cases(self, state, date, place_type):
        cases = self.Caso.objects.filter(
            state=state,
            date__lt=date,
            place_type=place_type,
        ).iterator()

        place_key_func = lambda row: (row.place_type, row.state, row.city)  # noqa
        order_func = lambda row: row.order_for_place  # noqa
        cases = sorted(cases, key=place_key_func)

        result = []
        for place_key, entries in groupby(cases, key=place_key_func):
            entries = sorted(entries, key=order_func, reverse=True)
            result.append(entries[0])

        if place_type == "state" and result:
            assert len(result) == 1
            result = result[0]

        return result
