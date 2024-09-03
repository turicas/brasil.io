from django.db import models
import django_filters

from elections.models import Candidacy


class CandidacyFilterSet(django_filters.FilterSet):
    ano = django_filters.NumberFilter("ano")
    uf = django_filters.CharFilter("sigla_unidade_federativa")
    cargo = django_filters.CharFilter("cargo_slug")
    partido = django_filters.CharFilter("sigla_partido", lookup_expr="iexact")
    q = django_filters.CharFilter(method="full_search")

    class Meta:
        model = Candidacy
        fields = ("ano", "uf", "cargo", "partido",)

    def full_search(self, queryset, name, value):
        # Check filter field
        if self.data.get("t") == "name":
            query_filter = (
                models.Q(nome_urna__unaccent__icontains=value)
                | models.Q(nome__unaccent__icontains=value)  # noqa
            )
        else:
            query_filter = models.Q(municipio__unaccent__icontains=value)

        return queryset.filter(query_filter)
