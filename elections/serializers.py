from rest_framework import serializers

from elections.models import Candidacy


class DetailCandidacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidacy
        fields = "__all__"
