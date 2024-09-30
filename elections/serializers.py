from django.urls import reverse
from rest_framework import serializers

from elections.date_utils import get_age
from elections.models import Candidacy
from elections.suggestions import format_city_name


class DetailCandidacySerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    data_nascimento = serializers.SerializerMethodField()
    region_filter_path = serializers.SerializerMethodField()

    class Meta:
        model = Candidacy
        fields = "__all__"

    def get_age(self, obj):
        _, age = get_age(obj.data_nascimento)
        return age

    def get_data_nascimento(self, obj):
        try:
            dt = obj.data_nascimento.strftime("%d/%m/%Y")
        except ValueError:
            dt = None

        return dt

    def get_region_filter_path(self, obj):
        try:
            path = (
                f"{format_city_name(obj.municipio.lower())}-{obj.sigla_unidade_federativa.upper()}"
            )
            full_path = reverse("elections:candidacy_list") + f"?q={path}"
        except Exception:
            full_path = None

        return full_path


class ListCandidacySerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField()
    name = serializers.CharField(source="nome")
    year = serializers.IntegerField(source="ano")
    cargo = serializers.CharField()
    municipio = serializers.CharField()
    uf = serializers.CharField(source="sigla_unidade_federativa")
    numero_urna = serializers.CharField()
    sigla_partido = serializers.CharField()

    class Meta:
        model = Candidacy
        fields = (
            "path",
            "name",
            "year",
            "cargo",
            "municipio",
            "uf",
            "numero_urna",
            "sigla_partido",
        )

    def get_path(self, obj):
        return (
            "/eleicoes/"
            f"{obj.ano}/"
            f"{obj.sigla_unidade_federativa.lower()}/"
            f"{obj.municipio_slug}/"
            f"{obj.cargo_slug}/"
            f"{obj.nome_urna_slug}/"
        )
