from rest_framework import serializers
from rest_framework.reverse import reverse

from core.models import Dataset, Field, Link, Table


class LinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Link
        fields = ('title', 'url')


class FieldSerializer(serializers.ModelSerializer):

    class Meta:
        model = Field
        fields = ('name', 'type')


class TableSerializer(serializers.ModelSerializer):
    fields = FieldSerializer(many=True, source='field_set')

    class Meta:
        model = Table
        fields = ('fields',)


class DatasetSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return reverse('api:dataset-detail', kwargs={'slug': obj.slug},
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
    schema = TableSerializer(source='get_table')

    def get_id(self, obj):
        return reverse('api:dataset-detail', kwargs={'slug': obj.slug},
                       request=self.context['request'])

    def get_data_url(self, obj):
        return reverse('api:dataset-data', kwargs={'slug': obj.slug},
                       request=self.context['request'])

    class Meta:
        model = Dataset
        fields = (
            'author_name', 'author_url', 'code_url', 'data_url', 'description',
            'id', 'license_name', 'license_url', 'links', 'name', 'slug',
            'source_name', 'source_url', 'schema'
        )


class GenericSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = '__all__'
