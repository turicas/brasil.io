from django.db import models
import django_filters

from elections.models import Candidacy


ALL_VALUE_NAME = "todos"


ESTADO_SIGLA_MAPPER = {
    "rio de janeiro": "RJ",
    "são paulo": "SP",
    "minas gerais": "MG",
    "rio de janeiro": "RJ",
    "bahia": "BA",
    "paraná": "PR",
    "rio grande do sul": "RS",
    "pernambuco": "PE",
    "ceará": "CE",
    "pará": "PA",
    "santa catarina": "SC",
    "goiás": "GO",
    "maranhão": "MA",
    "paraíba": "PB",
    "amazonas": "AM",
    "espírito santo": "ES",
    "mato grosso": "MT",
    "rio grande do norte": "RN",
    "piauí": "PI",
    "alagoas": "AL",
    "distrito federal": "DF",
    "mato grosso do sul": "MS",
    "sergipe": "SE",
    "rondônia": "RO",
    "tocantins": "TO",
    "acre": "AC",
    "amapá": "AM",
    "roraima": "RR",
}


class CandidacyFilterSet(django_filters.FilterSet):
    ano = django_filters.NumberFilter(method="filter_ano")
    uf = django_filters.CharFilter(method="filter_uf")
    cargo = django_filters.CharFilter(method="filter_cargo")
    partido = django_filters.CharFilter(method="filter_partido")
    q = django_filters.CharFilter(method="full_search")

    class Meta:
        model = Candidacy
        fields = ("ano", "uf", "cargo", "partido",)

    def filter_ano(self, queryset, name, value):
        if value == ALL_VALUE_NAME:
            return queryset

        return queryset.filter(ano=value)

    def filter_uf(self, queryset, name, value):
        if value.lower() == ALL_VALUE_NAME:
            return queryset

        estado_sigla = ESTADO_SIGLA_MAPPER.get(value.lower())

        return queryset.filter(sigla_unidade_federativa=estado_sigla)

    def filter_cargo(self, queryset, name, value):
        if value.lower() == ALL_VALUE_NAME:
            return queryset

        return queryset.filter(cargo_slug=value)

    def filter_partido(self, queryset, name, value):
        if value.lower() == ALL_VALUE_NAME:
            return queryset

        return queryset.filter(sigla_partido__iexact=value)

    def full_search(self, queryset, name, value):
        # Check filter field
        if self.data.get("t") == "nome":
            query_filter = (
                models.Q(nome_urna__unaccent__icontains=value)
                | models.Q(nome__unaccent__icontains=value)  # noqa
            )
        else:
            query_filter = models.Q(municipio__unaccent__icontains=value)

        return queryset.filter(query_filter)
