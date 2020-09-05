from django.db.models import Sum

from brazil_data.cities import ibge_data_per_state
from core.models import get_table_model
from covid19.serializers import CityCaseSerializer


class BaseStats:

    table_name = None

    def __init__(self, state=None):
        self.state = state

    def get_queryset(self):
        Model = get_table_model("covid19", self.table_name)
        qs = Model.objects
        if self.state:
            qs = qs.for_state(self.state)
        return qs


class CityStats(BaseStats):
    def get_queryset(self):
        qs = ibge_data_per_state()
        if self.state:
            qs = qs[self.state]
        else:
            result = []
            for cities in qs.values():
                result.extend(cities)
            qs = result

        return qs

    @property
    def number_of_cities(self):
        return len(self.get_queryset())

    @property
    def population(self):
        return sum(city.estimated_population for city in self.get_queryset())


class BoletimStats(BaseStats):

    table_name = "boletim"

    @property
    def total_reports(self):
        return self.get_queryset().count()


class CasoStats(BaseStats):

    table_name = "caso"

    @property
    def number_of_cities_with_cases(self):
        return self.get_queryset().latest_city_cases().count()

    @property
    def number_of_cities_with_deaths(self):
        return self.get_queryset().latest_city_cases().with_deaths().count()

    @property
    def affected_population(self):
        return (
            self.get_queryset().latest_city_cases().aggregate(population=Sum("estimated_population_2019"))["population"]
        )

    @property
    def confirmed(self):
        return self.get_queryset().latest_state_cases().aggregate(confirmed=Sum("confirmed"))["confirmed"]

    @property
    def deaths(self):
        return self.get_queryset().latest_state_cases().aggregate(deaths=Sum("deaths"))["deaths"]

    @property
    def per_city(self):
        return CityCaseSerializer(instance=self.get_queryset().latest_city_cases(), many=True).data
