import django_filters

from elections.models import Candidacy


class CandidacyFilterSet(django_filters.FilterSet):
    year = django_filters.NumberFilter("ano")
    uf = django_filters.CharFilter("sigla_unidade_federativa")

    class Meta:
        model = Candidacy
        fields = ("year", "uf",)
