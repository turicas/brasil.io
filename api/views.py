from django.shortcuts import get_object_or_404
from rest_framework import serializers, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

from core.models import Dataset, Table, Link
from api.serializers import (DatasetDetailSerializer,
                             DatasetSerializer,
                             GenericSerializer)

from . import paginators


class DatasetViewSet(viewsets.ModelViewSet):

    serializer_class = DatasetSerializer

    def get_queryset(self):
        return Dataset.objects.filter(show=True)

    def retrieve(self, request, slug):
        queryset = Dataset.objects.all()  # TODO: use self.get_queryset()
        obj = get_object_or_404(queryset, slug=slug)
        serializer = DatasetDetailSerializer(
            obj,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)


class DatasetDataListView(ListAPIView):

    pagination_class = paginators.LargeTablePageNumberPagination

    def get_model_class(self):
        dataset = get_object_or_404(Dataset, slug=self.kwargs['slug'])
        table = get_object_or_404(Table, dataset=dataset, name=self.kwargs['tablename'])
        return table.get_model()

    def get_queryset(self):
        querystring = self.request.query_params.copy()
        for pagination_key in ('limit', 'offset'):
            if pagination_key in querystring:
                del querystring[pagination_key]

        Model = self.get_model_class()
        queryset = Model.objects.filter_by_querystring(querystring)

        return queryset

    def get_serializer_class(self):
        Model = self.get_model_class()
        fields = sorted([field.name for field in Model._meta.fields
                         if field.name != 'search_data'])

        # TODO: move this monkey patch to a metaclass
        GenericSerializer.Meta.model = Model
        GenericSerializer.Meta.fields = fields
        return GenericSerializer

dataset_list = DatasetViewSet.as_view({'get': 'list'})
dataset_detail = DatasetViewSet.as_view({'get': 'retrieve'}, lookup_field='slug')
dataset_data = DatasetDataListView.as_view()
