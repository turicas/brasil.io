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
    data_url = serializers.SerializerMethodField()

    def get_data_url(self, obj):
        return reverse(
            'api:dataset-table-data',
            kwargs={'slug': obj.dataset.slug, 'tablename': obj.name},
            request=self.context['request']
        )

    class Meta:
        model = Table
        fields = ('fields', 'name', 'data_url', 'import_date')


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
    id = serializers.SerializerMethodField()
    links = LinkSerializer(many=True, source='link_set')
    tables = TableSerializer(many=True)
    collected_at = serializers.SerializerMethodField()

    def get_id(self, obj):
        return reverse('api:dataset-detail', kwargs={'slug': obj.slug},
                       request=self.context['request'])

    def get_collected_at(self, obj):
        return obj.last_version.collected_at

    class Meta:
        model = Dataset
        fields = (
            'author_name', 'author_url', 'code_url', 'description',
            'id', 'license_name', 'license_url', 'links', 'name', 'slug',
            'source_name', 'source_url', 'collected_at', 'tables',
        )


class GenericSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = '__all__'
