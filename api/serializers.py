from rest_framework import serializers
from rest_framework.reverse import reverse

from core.models import Dataset, Field, Link, Table, TableFile


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ("title", "url")


class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ("name", "type")


class TableFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableFile
        fields = ("file_url", "sha512sum", "filename", "size", "created_at")


class TableSerializer(serializers.ModelSerializer):
    fields = FieldSerializer(many=True, source="field_set")
    data_url = serializers.SerializerMethodField()

    def get_data_url(self, obj):
        return reverse(
            "v1:dataset-table-data",
            kwargs={"slug": obj.dataset.slug, "tablename": obj.name},
            request=self.context["request"],
        )

    class Meta:
        model = Table
        fields = ("fields", "name", "data_url", "import_date")


class DatasetSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    files_url = serializers.SerializerMethodField()

    def get_id(self, obj):
        return reverse("v1:dataset-detail", kwargs={"slug": obj.slug}, request=self.context["request"])

    def get_files_url(self, obj):
        return reverse("v1:dataset-file-list", kwargs={"slug": obj.slug}, request=self.context["request"])

    class Meta:
        model = Dataset
        fields = (
            "author_name",
            "author_url",
            "code_url",
            "description",
            "id",
            "license_name",
            "license_url",
            "name",
            "slug",
            "source_name",
            "source_url",
            "files_url",
        )


class DatasetDetailSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    links = LinkSerializer(many=True, source="link_set")
    tables = serializers.SerializerMethodField()
    collected_at = serializers.SerializerMethodField()
    files_url = serializers.SerializerMethodField()

    def get_id(self, obj):
        return reverse("v1:dataset-detail", kwargs={"slug": obj.slug}, request=self.context["request"])

    def get_collected_at(self, obj):
        return obj.last_version.collected_at

    def get_tables(self, obj):
        return TableSerializer(instance=obj.tables.api_enabled(), many=True, context=self.context).data

    def get_files_url(self, obj):
        return reverse("v1:dataset-file-list", kwargs={"slug": obj.slug}, request=self.context["request"])

    class Meta:
        model = Dataset
        fields = (
            "author_name",
            "author_url",
            "code_url",
            "description",
            "id",
            "license_name",
            "license_url",
            "links",
            "name",
            "slug",
            "source_name",
            "source_url",
            "collected_at",
            "tables",
            "files_url",
        )


class GenericSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = "__all__"
