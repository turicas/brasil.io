from django.utils.text import slugify
from rest_framework import serializers

from elections.models import Candidacy


class DetailCandidacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidacy
        fields = "__all__"


class ListCandidacySerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField()
    name = serializers.CharField(source="nome")
    year = serializers.IntegerField(source="ano")

    class Meta:
        model = Candidacy
        fields = ("path", "name", "year")

    def get_path(self, obj):
        return f"{obj.ano}/{obj.sigla_unidade_federativa}/{obj.cargo}/{slugify(obj.nome_urna)}/"
