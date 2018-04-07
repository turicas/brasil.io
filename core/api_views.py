from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers, viewsets
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import NotFound

from core import dynamic_models
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

    serializer_class = DatasetSerializer  # TODO: add pagination

    def get_queryset(self):
        return Dataset.objects.filter(slug__in=dynamic_models.model_attributes)

    def retrieve(self, request, slug):
        obj = get_object_or_404(self.get_queryset(), slug=slug)
        serializer = DatasetDetailSerializer(
            obj,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)


class DatasetDataListView(ListAPIView):

    def get_model_class(self):
        slug = self.kwargs['slug']
        if slug not in dynamic_models.model_attributes:
            return None
        return dynamic_models.get_model(slug)

    def get_queryset(self):
        # TODO: check if slug is in Dataset (if not, return 404)
        Model = self.get_model_class()
        slug = self.kwargs['slug']
        if Model is None:
            raise NotFound({'error': 'Data not found.'})

        qs = Model.objects.all()
        # TODO: inject `Meta.ordering` in Model creation class
        ordering = dynamic_models.model_attributes[slug].get('ordering', None)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def get_serializer_class(self):
        # TODO: create this serializer class inside `core.dynamic_models` (or
        # even inside a method on `cores.models.Dataset`)
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
