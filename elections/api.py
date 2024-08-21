import django_filters
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from elections.filters import CandidacyFilterSet
from elections.models import Candidacy
from elections.serializers import DetailCandidacySerializer, ListCandidacySerializer


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    page_size = 6


class CandidacyDetailAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get_queryset(self):
        return Candidacy.objects.all()

    def get(self, request, *args, **kwargs):
        candidacy = get_object_or_404(Candidacy)
        serializer = DetailCandidacySerializer(candidacy)
        return Response(data=dict())


class CandidacyListAPIView(ListAPIView):
    authentication_classes = []
    permission_classes = []
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = CandidacyFilterSet
    pagination_class = CustomPageNumberPagination
    serializer_class = ListCandidacySerializer

    def get_queryset(self):
        return Candidacy.objects.all()
