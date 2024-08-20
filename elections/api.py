from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from elections.models import Candidacy
from elections.serializers import DetailCandidacySerializer


class CandidacyAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get_queryset(self):
        return Candidacy.objects.all()

    def get(self, request, *args, **kwargs):
        candidacy = get_object_or_404(Candidacy)
        serializer = DetailCandidacySerializer(candidacy)
        return Response(data=dict())
