import datetime

from django.utils.text import slugify
from rest_framework import serializers


class CityCaseSerializer(serializers.Serializer):
    city = serializers.CharField()
    city_ibge_code = serializers.IntegerField()
    city_str = serializers.SerializerMethodField()
    confirmed = serializers.SerializerMethodField()
    confirmed_per_100k_inhabitants = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    date_str = serializers.SerializerMethodField()
    death_rate_percent = serializers.SerializerMethodField()
    deaths = serializers.SerializerMethodField()
    estimated_population_2019 = serializers.IntegerField()
    state = serializers.CharField()

    def get_confirmed(self, case):
        return case.confirmed or 0

    def get_confirmed_per_100k_inhabitants(self, case):
        return case.confirmed_per_100k_inhabitants or 0

    def get_deaths(self, case):
        return case.deaths or 0

    def get_death_rate_percent(self, case):
        return (case.death_rate or 0) * 100

    def get_date_str(self, case):
        return str(case.date)

    def get_date(self, case):
        year, month, day = str(case.date).split("-")
        return datetime.date(int(year), int(month), int(day))

    def get_city_str(self, case):
        return slugify(case.city).replace("-", " ")
