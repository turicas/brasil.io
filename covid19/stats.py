import datetime

from cached_property import cached_property

from django.db.models import Max, Sum
from django.utils.text import slugify

from core.models import get_table_model


class Covid19Stats:

    @property
    def Boletim(self):
        return get_table_model("covid19", "boletim")

    @property
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
        )

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
        value_keys = ("confirmed", "deaths", "death_rate_percent", "confirmed_per_100k_inhabitants")
        result = {}
        # TODO: what should we do about "Importados/Indefinidos"?
        for city_case in self.city_cases.filter(city_ibge_code__isnull=False):
            row = {
                "city": city_case.city,
                "city_ibge_code": city_case.city_ibge_code,
                "confirmed": city_case.confirmed,
                "confirmed_per_100k_inhabitants": city_case.confirmed_per_100k_inhabitants,
                "date": city_case.date,
                "death_rate": city_case.death_rate,
                "deaths": city_case.deaths,
                "estimated_population_2019": city_case.estimated_population_2019,
                "state": city_case.state,
            }
            row["death_rate_percent"] = (row.pop("death_rate") or 0) * 100
            for key in value_keys:
                row[key] = row[key] or 0
            row["date_str"] = str(row["date"])
            row["city_str"] = slugify(row["city"]).replace("-", " ")
            year, month, day = row["date_str"].split("-")
            row["date"] = datetime.date(int(year), int(month), int(day))
            result[int(row["city_ibge_code"])] = row
        max_values = {
            key: max(row[key] for row in result.values())
            for key in value_keys
        }
        return {"cities": result, "max": max_values}
