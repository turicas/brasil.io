from collections import Sequence

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from api.serializers import DatasetDetailSerializer, DatasetSerializer, GenericSerializer
from core.filters import parse_querystring
from core.forms import get_table_dynamic_form
from core.models import Dataset, Table
from core.templatetags.utils import obfuscate

from . import paginators


class DatasetViewSet(viewsets.ModelViewSet):

    serializer_class = DatasetSerializer

    def get_queryset(self):
        return Dataset.objects.filter(show=True)

    def retrieve(self, request, slug):
        queryset = Dataset.objects.all()  # TODO: use self.get_queryset()
        obj = get_object_or_404(queryset, slug=slug)
        serializer = DatasetDetailSerializer(obj, context=self.get_serializer_context(),)
        return Response(serializer.data)


class InvalidFiltersException(Exception):
    def __init__(self, errors_list):
        self.errors_list = errors_list


class DatasetDataListView(ListAPIView):

    pagination_class = paginators.LargeTablePageNumberPagination

    def get_table(self):
        dataset = get_object_or_404(Dataset, slug=self.kwargs["slug"])
        return get_object_or_404(Table.objects.api_enabled(), dataset=dataset, name=self.kwargs["tablename"])

    def get_model_class(self):
        return self.get_table().get_model()

    def get_queryset(self):
        querystring = self.request.query_params.copy()
        for pagination_key in ("limit", "offset"):
            if pagination_key in querystring:
                del querystring[pagination_key]

        Model = self.get_model_class()
        query, search_query, order_by = parse_querystring(querystring)

        DynamicForm = get_table_dynamic_form(self.get_table())
        filter_form = DynamicForm(data=query)
        if filter_form.is_valid():
            query = {k: v for k, v in filter_form.cleaned_data.items() if v != ""}
        else:
            raise InvalidFiltersException(filter_form.errors)

        return Model.objects.composed_query(query, search_query, order_by)

    def get_serializer_class(self):
        table = self.get_table()
        Model = self.get_model_class()
        fields = sorted([field.name for field in table.fields if field.name != "search_data" and field.show])

        # TODO: move this monkey patch to a metaclass
        GenericSerializer.Meta.model = Model
        GenericSerializer.Meta.fields = fields
        return GenericSerializer

    def get_serializer(self, *args, **kwargs):
        self.get_model_class()  # TODO: avoid to call it twice
        obfuscate_fields = [field.name for field in self.get_table().fields if field.obfuscate and field.show]
        if obfuscate_fields:
            objects = args[0]
            if not isinstance(objects, Sequence):
                objects = [objects]
            for obj in objects:
                for field_name in obfuscate_fields:
                    value = obfuscate(getattr(obj, field_name))
                    setattr(obj, field_name, value)

        return super().get_serializer(*args, **kwargs)

    def handle_exception(self, exc):
        if isinstance(exc, InvalidFiltersException):
            return Response(exc.errors_list, status=400)
        else:
            return super().handle_exception(exc)


dataset_list = DatasetViewSet.as_view({"get": "list"})
dataset_detail = DatasetViewSet.as_view({"get": "retrieve"}, lookup_field="slug")
dataset_data = DatasetDataListView.as_view()
