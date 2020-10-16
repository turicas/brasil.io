import hashlib
import random
import string
from collections import OrderedDict, namedtuple
from textwrap import dedent
from urllib.parse import urlparse

import django.contrib.postgres.indexes as pg_indexes
import django.db.models.indexes as django_indexes
from cachalot.api import invalidate
from cached_property import cached_property
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVectorField
from django.db import connection, models, transaction
from django.db.models import F
from django.db.models.signals import post_delete, pre_delete
from django.db.utils import ProgrammingError
from django.urls import reverse
from markdownx.models import MarkdownxField
from rows import fields as rows_fields

from core import dynamic_models
from core.filters import DynamicModelFilterProcessor
from utils.classes import subclasses
from utils.file_info import human_readable_size

DYNAMIC_MODEL_REGISTRY = {}


def make_index_name(tablename, index_type, fields):
    idx_hash = hashlib.md5(f'{tablename} {index_type} {", ".join(sorted(fields))}'.encode("ascii")).hexdigest()
    tablename = tablename.replace("data_", "").replace("-", "")[:12]
    return f"idx_{tablename}_{index_type[0]}{idx_hash[-12:]}"


class DatasetTableModelMixin:
    """Brasil.IO-specific methods for dataset tables' dynamic Models"""

    @classmethod
    def tablename(cls):
        return cls._meta.db_table

    @classmethod
    def analyse_table(cls):
        with connection.cursor() as cursor:
            cursor.execute("VACUUM ANALYSE {}".format(cls.tablename()))

    @classmethod
    def get_trigger_name(cls):
        return f"tgr_tsv_{cls.tablename()}"

    @classmethod
    def create_triggers(cls):
        trigger_name = cls.get_trigger_name()
        fieldnames = ", ".join(cls.extra["search"])
        query = dedent(
            f"""
            CREATE TRIGGER {trigger_name}
                BEFORE INSERT OR UPDATE
                ON {cls.tablename()}
                FOR EACH ROW EXECUTE PROCEDURE
                tsvector_update_trigger(search_data, 'pg_catalog.portuguese', {fieldnames})
        """
        ).strip()
        # TODO: replace pg_catalog.portuguese with dataset language
        with connection.cursor() as cursor:
            cursor.execute(query)


class DatasetTableModelQuerySet(models.QuerySet):
    def search(self, search_query):
        qs = self
        search_fields = self.model.extra["search"]
        if search_query and search_fields:
            words = search_query.split()
            config = "pg_catalog.portuguese"  # TODO: get from self.model.extra
            query = None
            for word in set(words):
                if not word:
                    continue
                if query is None:
                    query = SearchQuery(word, config=config)
                else:
                    query = query & SearchQuery(word, config=config)
            qs = qs.annotate(search_rank=SearchRank(F("search_data"), query)).filter(search_data=query)
            # Using `qs.query.add_ordering` will APPEND ordering fields instead
            # of OVERWRITTING (as in `qs.order_by`).
            qs.query.add_ordering("-search_rank")
        return qs

    def apply_filters(self, filtering):
        # TODO: filtering must be based on field's settings, not on models
        # settings.
        model_filtering = self.model.extra["filtering"]
        processor = DynamicModelFilterProcessor(filtering, model_filtering)
        return self.filter(**processor.filters)

    def apply_ordering(self, query):
        qs = self
        # TODO: may use Model's meta "ordering" instead of extra["ordering"]
        model_ordering = self.model.extra["ordering"]
        model_filtering = self.model.extra["filtering"]
        allowed_fields = set(model_ordering + model_filtering)
        clean_allowed = [field.replace("-", "").strip().lower() for field in allowed_fields]
        ordering_query = [field for field in query if field.replace("-", "") in clean_allowed]
        # Using `qs.query.add_ordering` will APPEND ordering fields instead of
        # OVERWRITTING (as in `qs.order_by`).
        if ordering_query:
            qs.query.add_ordering(*ordering_query)
        elif model_ordering:
            qs.query.add_ordering(*model_ordering)

        return qs

    def composed_query(self, filter_query=None, search_query=None, order_by=None):
        qs = self
        if search_query:
            qs = qs.search(search_query)
        if filter_query:
            qs = qs.apply_filters(filter_query)
        return qs.apply_ordering(order_by or [])

    def count(self):
        if getattr(self, "_count", None) is not None:
            return self._count

        query = self.query
        if not query.where:  # TODO: check groupby etc.
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT reltuples FROM pg_class WHERE relname = %s", [query.model._meta.db_table],
                    )
                    self._count = int(cursor.fetchone()[0])
            except Exception:
                self._count = super().count()
        else:
            self._count = super().count()

        return self._count


class DatasetQuerySet(models.QuerySet):
    def api_visible(self):
        return self.filter(show=True)


class Dataset(models.Model):
    objects = DatasetQuerySet.as_manager()

    author_name = models.CharField(max_length=255, null=False, blank=False)
    author_url = models.URLField(max_length=2000, null=True, blank=True)
    code_url = models.URLField(max_length=2000, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    icon = models.CharField(max_length=31, null=False, blank=False)
    license_name = models.CharField(max_length=255, null=False, blank=False)
    license_url = models.URLField(max_length=2000, null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    show = models.BooleanField(null=False, blank=False, default=False)
    slug = models.SlugField(max_length=50, null=False, blank=False)
    source_name = models.CharField(max_length=255, null=False, blank=False)
    source_url = models.URLField(max_length=2000, null=False, blank=False)

    @property
    def tables(self):
        # By now we're ignoring version - just take the last one
        version = self.get_last_version()
        return self.table_set.filter(version=version).order_by("name")

    @property
    def all_tables(self):
        # By now we're ignoring version - just take the last one
        version = self.get_last_version()
        return Table.with_hidden.filter(version=version).order_by("name")

    @property
    def last_version(self):
        return self.get_last_version()

    @property
    def files_url(self):
        return reverse("core:dataset-files-detail", args=[self.slug])

    @property
    def detail_url(self):
        return reverse("core:dataset-detail", args=[self.slug])

    @property
    def tables_files(self):
        return sorted([TableFile.objects.get_most_recent_for_table(t) for t in self.tables], key=lambda f: f.filename)

    @property
    def sha512sums(self):
        """
        Return a TableFile-like object with the SHA512SUMS from all tables
        """
        FileInfo = namedtuple("FileInfo", ("filename", "file_url", "readable_size", "sha512sum", "content"))
        sha_sum = hashlib.sha512()
        content = ""

        for table_file in self.tables_files:
            sha_sum.update(content.encode())
            content += f"{table_file.sha512sum}  {table_file.filename}\n"

        fname = settings.MINIO_DATASET_SHA512SUMS_FILENAME
        url = f"{settings.AWS_S3_ENDPOINT_URL}{settings.MINIO_STORAGE_DATASETS_BUCKET_NAME}/{self.slug}/{fname}"
        return FileInfo(
            filename=fname,
            file_url=url,
            readable_size=human_readable_size(len(content.encode())),
            sha512sum=sha_sum.hexdigest(),
            content=content,
        )

    @property
    def all_files(self):
        files = self.tables_files
        return [] if not files else files + [self.sha512sums]

    def get_table(self, tablename, allow_hidden=False):
        if allow_hidden:
            return Table.with_hidden.for_dataset(self).named(tablename)
        else:
            return Table.objects.for_dataset(self).named(tablename)

    def get_default_table(self):
        return Table.objects.for_dataset(self).default()

    def __str__(self):
        name = self.name or self.slug
        if self.author_name:
            name += ", by: " + self.author_name
        if self.source_name:
            name += ", source: " + self.source_name
        return name

    def get_model_declaration(self):
        version = self.version_set.order_by("order").last()
        table = self.table_set.get(version=version, default=True)
        return table.get_model_declaration()

    def get_last_version(self):
        return self.version_set.order_by("order").last()


class Link(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=False, blank=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    url = models.URLField(max_length=2000, null=False, blank=False)

    def __str__(self):
        domain = urlparse(self.url).netloc
        return "{} ({})".format(self.title, domain)


class Version(models.Model):
    collected_at = models.DateField(null=False, blank=False)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=False, blank=False)
    download_url = models.URLField(max_length=2000, null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    order = models.PositiveIntegerField(null=False, blank=False)

    def __str__(self):
        return "{}.{} (order: {})".format(self.dataset.slug, self.name, self.order)


class TableQuerySet(models.QuerySet):
    def for_dataset(self, dataset):
        if isinstance(dataset, str):
            kwargs = {"dataset__slug": dataset}
        else:
            kwargs = {"dataset": dataset}
        return self.filter(**kwargs)

    def default(self):
        return self.get(default=True)

    def named(self, name):
        return self.get(name=name)

    def api_enabled(self):
        return self.filter(api_enabled=True)


class ActiveTableManager(models.Manager):
    """
    This manager is the main one for the Table model and it excludes hidden tables by default
    """

    def get_queryset(self):
        return super().get_queryset().filter(hidden=False)


class AllTablesManager(models.Manager):
    """
    This manager is used to fetch all tables in the database, including the hidden ones
    """


class Table(models.Model):
    objects = ActiveTableManager.from_queryset(TableQuerySet)()
    with_hidden = AllTablesManager.from_queryset(TableQuerySet)()

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=False, blank=False)
    default = models.BooleanField(null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    options = models.JSONField(null=True, blank=True)
    ordering = ArrayField(models.CharField(max_length=63), null=False, blank=False)
    filtering_fields = ArrayField(models.CharField(max_length=63), null=True, blank=True)
    search_fields = ArrayField(models.CharField(max_length=63), null=True, blank=True)
    version = models.ForeignKey(Version, on_delete=models.CASCADE, null=False, blank=False)
    import_date = models.DateTimeField(null=True, blank=True)
    description = MarkdownxField(null=True, blank=True)
    hidden = models.BooleanField(default=False)
    api_enabled = models.BooleanField(default=True)

    def __str__(self):
        return "{}.{}.{}".format(self.dataset.slug, self.version.name, self.name)

    @property
    def filtering(self):
        return [f.name for f in self.fields.frontend_filters()]

    @property
    def collect_date(self):
        return self.version.collected_at

    @property
    def data_table(self):
        return self.data_tables.get_current_active()

    @property
    def db_table(self):
        return self.data_table.db_table_name

    @property
    def fields(self):
        return self.field_set.all()

    @property
    def search(self):
        return [f.name for f in self.fields.searchable()]

    @property
    def enabled(self):
        return not self.hidden

    @property
    def schema(self):
        db_fields_to_rows_fields = {
            "binary": rows_fields.BinaryField,
            "bool": rows_fields.BoolField,
            "date": rows_fields.DateField,
            "datetime": rows_fields.DatetimeField,
            "decimal": rows_fields.DecimalField,
            "email": rows_fields.EmailField,
            "float": rows_fields.FloatField,
            "integer": rows_fields.IntegerField,
            "json": rows_fields.JSONField,
            "string": rows_fields.TextField,
            "text": rows_fields.TextField,
        }
        return OrderedDict(
            [
                (n, db_fields_to_rows_fields.get(t, rows_fields.Field))
                for n, t in self.fields.values_list("name", "type")
            ]
        )

    @property
    def model_name(self):
        full_name = self.dataset.slug + "-" + self.name
        parts = full_name.replace("_", "-").replace(" ", "-").split("-")
        return "".join([word.capitalize() for word in parts])

    @cached_property
    def dynamic_table_config(self):
        return DynamicTableConfig.get_dynamic_table_customization(self.dataset.slug, self.name)

    def get_dynamic_model_managers(self):
        managers = {"objects": DatasetTableModelQuerySet.as_manager()}

        if self.dynamic_table_config:
            managers.update(self.dynamic_table_config.get_model_managers())

        return managers

    def get_dynamic_model_mixins(self):
        mixins = [DatasetTableModelMixin]
        custom_mixins = [] if not self.dynamic_table_config else self.dynamic_table_config.get_model_mixins()
        return custom_mixins + mixins

    def get_field(self, name):
        return self.fields.get(name=name)

    def get_model(self, cache=True, data_table=None):
        # TODO: the current dynamic model registry is handled by Brasil.IO's
        # code but it needs to be delegated to dynamic_models.

        data_table = data_table or self.data_table
        db_table = data_table.db_table_name

        # TODO: limit the max number of items in DYNAMIC_MODEL_REGISTRY
        cache_key = (self.id, db_table)
        if cache and cache_key in DYNAMIC_MODEL_REGISTRY:
            return DYNAMIC_MODEL_REGISTRY[cache_key]

        # TODO: unregister the model in Django if already registered (cache_key
        # in DYNAMIC_MODEL_REGISTRY and not cache)
        fields = {field.name: field.field_class for field in self.fields}
        fields["search_data"] = SearchVectorField(null=True)
        ordering = self.ordering or []
        filtering = self.filtering or []
        search = self.search or []
        indexes = []
        # TODO: add has_choices fields also
        if ordering:
            indexes.append(django_indexes.Index(name=make_index_name(db_table, "order", ordering), fields=ordering,))
        if filtering:
            for field_name in filtering:
                if ordering == [field_name]:
                    continue
                indexes.append(
                    django_indexes.Index(name=make_index_name(db_table, "filter", [field_name]), fields=[field_name])
                )
        if search:
            indexes.append(
                pg_indexes.GinIndex(name=make_index_name(db_table, "search", ["search_data"]), fields=["search_data"])
            )

        managers = self.get_dynamic_model_managers()
        mixins = self.get_dynamic_model_mixins()
        meta = {"ordering": ordering, "indexes": indexes, "db_table": db_table}

        Model = dynamic_models.create_model_class(
            name=self.model_name, module="core.models", fields=fields, mixins=mixins, meta=meta, managers=managers,
        )
        Model.extra = {
            "filtering": filtering,
            "ordering": ordering,
            "search": search,
            "table": self,
        }
        DYNAMIC_MODEL_REGISTRY[cache_key] = Model
        return Model

    def get_model_declaration(self):
        Model = self.get_model()
        return dynamic_models.model_source_code(Model)

    def invalidate_cache(self):
        invalidate(self.db_table)


class DynamicTableConfig:
    """
    Helper base class used by core.models.Table to fetch for dynamic models' customization
    """

    @classmethod
    def get_dynamic_table_customization(cls, dataset_slug, table_name):
        CustomConfig = None
        for subclass in subclasses(cls):
            valid_implementation_conditions = [
                getattr(subclass, "dataset_slug", None) == dataset_slug,
                getattr(subclass, "table_name", None) == table_name,
            ]
            if all(valid_implementation_conditions):
                CustomConfig = subclass
                break

        return None if not CustomConfig else CustomConfig()

    @classmethod
    def get_model(cls):
        # TODO add flag to with_hidden
        table = Table.with_hidden.for_dataset(cls.dataset_slug).named(cls.table_name)
        return table.get_model()

    def get_model_mixins(self):
        return []

    def get_model_managers(self):
        return {}


class FieldQuerySet(models.QuerySet):
    def for_table(self, table):
        return self.filter(table=table)

    def choiceables(self):
        return self.frontend_filters().filter(has_choices=True)

    def frontend_filters(self):
        return self.filter(frontend_filter=True)

    def searchable(self):
        return self.filter(searchable=True)


class Field(models.Model):
    objects = FieldQuerySet.as_manager()

    TYPE_CHOICES = [(value, value) for value in dynamic_models.FIELD_TYPES.keys()]

    choices = models.JSONField(null=True, blank=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    frontend_filter = models.BooleanField(null=False, blank=True, default=False)
    searchable = models.BooleanField(null=False, blank=True, default=False)
    has_choices = models.BooleanField(null=False, blank=True, default=False)
    link_template = models.TextField(max_length=2000, null=True, blank=True)
    order = models.PositiveIntegerField(null=False, blank=False)
    null = models.BooleanField(null=False, blank=True, default=True)
    name = models.CharField(max_length=63)
    options = models.JSONField(null=True, blank=True)
    obfuscate = models.BooleanField(null=False, blank=True, default=False)
    show = models.BooleanField(null=False, blank=True, default=True)
    show_on_frontend = models.BooleanField(null=False, blank=True, default=False)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, null=False, blank=False)
    title = models.CharField(max_length=63)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES, null=False, blank=False)
    version = models.ForeignKey(Version, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        options = self.options or {}
        options_str = ", ".join("{}={}".format(key, repr(value)) for key, value in options.items())
        return "{}.{}({})".format(self.table.name, self.name, options_str)

    @property
    def field_class(self):
        kwargs = self.options or {}
        kwargs["null"] = self.null
        return dynamic_models.FIELD_TYPES[self.type](**kwargs)

    def options_text(self):
        if not self.options:
            return ""

        return ", ".join(["{}={}".format(key, repr(value)) for key, value in self.options.items()])

    def update_choices(self, data_table=None):
        Model = self.table.get_model(data_table=data_table)
        choices = Model.objects.order_by(self.name).distinct(self.name).values_list(self.name, flat=True)
        self.choices = {"data": [str(value) for value in choices]}


def get_table(dataset_slug, tablename, allow_hidden=False):
    qs = Table.objects
    if allow_hidden:
        qs = Table.with_hidden
    return qs.for_dataset(dataset_slug).named(tablename)


def get_table_model(dataset_slug, tablename):
    # TODO: this function is just a shortcut and should be removed
    table = get_table(dataset_slug, tablename, allow_hidden=True)
    ModelClass = table.get_model(cache=True)

    return ModelClass


class DataTableQuerySet(models.QuerySet):
    def get_current_active(self):
        return self.active().most_recent()

    def most_recent(self):
        return self.order_by("-created_at").first()

    def inactive(self):
        return self.filter(active=False)

    def active(self):
        return self.filter(active=True)

    def for_dataset(self, dataset_slug):
        return self.filter(table__dataset__slug=dataset_slug)


class DataTable(models.Model):
    objects = DataTableQuerySet.as_manager()

    created_at = models.DateTimeField(auto_now_add=True)
    table = models.ForeignKey(Table, related_name="data_tables", on_delete=models.SET_NULL, null=True)
    db_table_name = models.TextField()
    active = models.BooleanField(default=False)

    def __str__(self):
        return f"DataTable: {self.db_table_name}"

    @property
    def admin_url(self):
        return reverse("admin:core_datatable_change", args=[self.id])

    @classmethod
    def new_data_table(cls, table, suffix_size=8):
        db_table_suffix = "".join(random.choice(string.ascii_lowercase) for i in range(suffix_size))
        db_table_name = "data_{}_{}".format(table.dataset.slug.replace("-", ""), table.name.replace("_", ""))
        if db_table_suffix:
            db_table_name += f"_{db_table_suffix}"
        return cls(table=table, db_table_name=db_table_name)

    def activate(self, drop_inactive_table=False):
        with transaction.atomic():
            prev_data_table = self.table.data_table
            if prev_data_table:
                prev_data_table.deactivate(drop_table=drop_inactive_table)
            self.active = True
            self.save()

    def deactivate(self, drop_table=False, activate_most_recent=False):
        with transaction.atomic():
            if activate_most_recent and self.active:
                most_recent = self.table.data_tables.exclude(id=self.id).inactive().most_recent()
                if most_recent:
                    most_recent.activate(drop_inactive_table=drop_table)
                    return

            self.active = False
            self.save()
            if drop_table:
                self.delete_data_table()

    def delete_data_table(self):
        Model = self.table.get_model(cache=False, data_table=self)
        try:
            Model.delete_table()
        except ProgrammingError:  # model does not exist
            pass


def prevent_active_data_table_deletion(sender, instance, **kwargs):
    if instance.active:
        msg = f"{instance} is active and can not be deleted. Deactivate it first."
        raise RuntimeError(msg)


def clean_associated_data_base_table(sender, instance, **kwargs):
    instance.delete_data_table()


pre_delete.connect(prevent_active_data_table_deletion, sender=DataTable)
post_delete.connect(clean_associated_data_base_table, sender=DataTable)


class TableFileQuerySet(models.QuerySet):
    def get_most_recent_for_table(self, table):
        table_file = self.filter(table=table).first()
        if not table_file:
            raise TableFile.DoesNotExist(f"For table {table}")
        return table_file


class TableFile(models.Model):
    objects = TableFileQuerySet.as_manager()

    table = models.ForeignKey(Table, related_name="table_file", on_delete=models.CASCADE)
    file_url = models.URLField()
    sha512sum = models.CharField(max_length=128)
    filename = models.TextField()
    size = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def readable_size(self):
        return human_readable_size(int(self.size))

    @property
    def admin_url(self):
        return reverse("admin:core_tablefile_change", args=[self.id])


class DataUrlRedirect(models.Model):
    dataset_prev = models.SlugField(default="")
    dataset_dest = models.SlugField(default="")

    tablename_prev = models.SlugField(default="")
    tablename_dest = models.SlugField(default="")

    field_prev = models.SlugField(default="")
    field_dest = models.SlugField(default="")

    @property
    def redirect_map(self):
        dataset_url_names = [
            "core:dataset-detail",
            "core:dataset-files-detail",
            "api-v1:dataset-detail",
        ]

        return {reverse(n, args=[self.dataset_prev]): reverse(n, args=[self.dataset_dest]) for n in dataset_url_names}

    @classmethod
    def redirect_from(cls, request):
        path = request.path
        redirects = {}

        for data_url_redirect in cls.objects.all().iterator():
            redirects.update(**data_url_redirect.redirect_map)

        # Order prefixes begining by the most complex ones
        for url_prefix in sorted(redirects, reverse=True):
            if path.startswith(url_prefix):
                redirect_url_prefix = redirects[url_prefix]
                return path.replace(url_prefix, redirect_url_prefix)
