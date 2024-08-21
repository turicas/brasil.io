from rest_framework import serializers

from elections.models import Candidacy


class DetailCandidacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidacy
        fields = "__all__"


class ListCandidacySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="nome")
    year = serializers.IntegerField(source="ano")

    class Meta:
        model = Candidacy
        fields = ("id", "name", "year")
