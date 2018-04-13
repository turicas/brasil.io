from django.shortcuts import get_object_or_404
from rest_framework import serializers, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

from core import paginators
from core.models import Dataset, Link


class LinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Link
        fields = ('title', 'url')


class DatasetSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return reverse('core:dataset', kwargs={'slug': obj.slug},
                       request=self.context['request'])

    class Meta:
        model = Dataset
        fields = (
            'author_name', 'author_url', 'code_url', 'description', 'id',
            'license_name', 'license_url', 'name', 'slug', 'source_name',
            'source_url',
        )


class DatasetDetailSerializer(serializers.ModelSerializer):
    data_url = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    links = LinkSerializer(many=True, source='link_set')
    # TODO: add schema

    def get_id(self, obj):
        return reverse('core:dataset', kwargs={'slug': obj.slug},
                       request=self.context['request'])

    def get_data_url(self, obj):
        return reverse('core:dataset-data', kwargs={'slug': obj.slug},
                       request=self.context['request'])

    class Meta:
        model = Dataset
        fields = (
            'author_name', 'author_url', 'code_url', 'data_url', 'description',
            'id', 'license_name', 'license_url', 'links', 'name', 'slug',
            'source_name', 'source_url',
        )


class DatasetViewSet(viewsets.ModelViewSet):

    serializer_class = DatasetSerializer

    def get_queryset(self):
        return Dataset.objects.all()

    def retrieve(self, request, slug):
        obj = get_object_or_404(self.get_queryset(), slug=slug)
        serializer = DatasetDetailSerializer(
            obj,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)


class DatasetDataListView(ListAPIView):

    pagination_class = paginators.LargeTablePageNumberPagination

    def get_model_class(self):
        dataset = get_object_or_404(Dataset, slug=self.kwargs['slug'])
        return dataset.get_last_data_model()

    def get_queryset(self):
        querystring = self.request.query_params.copy()
        for pagination_key in ('limit', 'offset'):
            if pagination_key in querystring:
                del querystring[pagination_key]
        order_by = querystring.pop('order-by', [''])
        Model = self.get_model_class()
        queryset = Model.objects.all()

        if querystring:
            queryset = queryset.apply_filters(querystring)

        order_by = [field.strip().lower()
                    for field in order_by[0].split(',')
                    if field.strip()]
        queryset = queryset.apply_ordering(order_by)

        return queryset

    def get_serializer_class(self):
        Model = self.get_model_class()
        fields = sorted([field.name for field in Model._meta.fields])

        # TODO: move this monkey patch to a metaclass
        GenericSerializer.Meta.model = Model
        GenericSerializer.Meta.fields = fields
        return GenericSerializer

class GenericSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = '__all__'

dataset_list = DatasetViewSet.as_view({'get': 'list'})
dataset_detail = DatasetViewSet.as_view({'get': 'retrieve'}, lookup_field='slug')
dataset_data = DatasetDataListView.as_view()
