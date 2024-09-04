from datetime import date, datetime

from django.utils.text import slugify
from rest_framework import serializers

from elections.models import Candidacy


class DetailCandidacySerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    data_nascimento = serializers.SerializerMethodField()

    class Meta:
        model = Candidacy
        fields = "__all__"

    def get_age(self, obj):
        today = date.today()
        try:
            dtob = datetime.strptime(obj.data_nascimento, "%Y-%m-%d").date()
            age = today.year - dtob.year - ((today.month, today.day) < (dtob.month, dtob.day))
        except Exception:
            return None

        return age

    def get_data_nascimento(self, obj):
        try:
            dt = datetime.strptime(obj.data_nascimento, "%Y-%m-%d")
            dt = dt.strftime("%d/%m/%Y")
        except ValueError:
            dt = None

        return dt


class ListCandidacySerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField()
    name = serializers.CharField(source="nome")
    year = serializers.IntegerField(source="ano")

    class Meta:
        model = Candidacy
        fields = ("path", "name", "year")

    def get_path(self, obj):
        return (
            "/politic/"
            f"{obj.ano}/"
            f"{obj.sigla_unidade_federativa.lower()}/"
            f"{slugify(obj.cargo)}/"
            f"{slugify(obj.nome_urna)}/"
        )
