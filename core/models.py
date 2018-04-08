from urllib.parse import urlparse

from django.db import connection, models
from django.contrib.postgres.fields import ArrayField, JSONField


DYNAMIC_MODEL_REGISTRY = {}

class DynamicModelMixin:

    @classmethod
    def create_table(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(cls)

    @classmethod
    def delete_table(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(cls)


class DynamicModelQuerySet(models.QuerySet):

    def apply_filters(self, filtering):
        qs = self
        model_filtering = self.model.extra['filtering']
        if model_filtering is not None:
            for field_name in model_filtering:
                value = filtering.get(field_name, None)
                if value is not None:
                    qs = qs.filter(**{field_name: value})

            search_query = filtering.get('search', None)
            if search_query is not None:
                search_vector = SearchVector(*model_filtering)
                qs = qs.annotate(search=search_vector)\
                       .filter(search=search_query)
        return qs

    def apply_ordering(self, query):
        qs = self
        model_ordering = self.model.extra['ordering']
        if model_ordering is not None:
            clean_ordering = [field.replace('-', '').strip().lower()
                              for field in model_ordering]
            ordering_query = [field for field in query
                              if field in clean_ordering]
            if ordering_query:
                qs = qs.order_by(*ordering_query)
            else:
                qs = qs.order_by(*model_ordering)

        return qs


class Dataset(models.Model):
    author_name = models.CharField(max_length=255, null=False, blank=False)
    author_url = models.URLField(max_length=2000, null=True, blank=True)
    code_url = models.URLField(max_length=2000, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    license_name = models.CharField(max_length=255, null=False, blank=False)
    license_url = models.URLField(max_length=2000, null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    slug = models.SlugField(max_length=50, null=False, blank=False)
    source_name = models.CharField(max_length=255, null=False, blank=False)
    source_url = models.URLField(max_length=2000, null=False, blank=False)

    def __str__(self):
        return f'{self.name} (by {self.author_name}, source: {self.source_name})'

    def get_last_data_model(self):
        model_name = ''.join([word.capitalize()
                              for word in self.slug.split('-')])
        if self.slug not in DYNAMIC_MODEL_REGISTRY:
            version = self.version_set.order_by('order').last()
            print(version)
            table = self.table_set.get(version=version, default=True)
            fields = {field.name: field.field_class
                      for field in self.field_set.filter(table=table)}
            ordering = table.ordering or []
            filtering = table.filtering or []
            indexes = []
            if ordering:
                indexes.append(models.Index(fields=ordering))
            for field_name in filtering:
                indexes.append(models.Index(fields=[field_name]))
            Options = type(
                'Meta',
                (object,),
                {
                    'ordering': ordering,
                    'indexes': indexes,
                },
            )
            Model = type(
                model_name,
                (DynamicModelMixin, models.Model,),
                {
                    '__module__': 'core.models',
                    'Meta': Options,
                    'objects': DynamicModelQuerySet.as_manager(),
                    **fields,
                },
            )
            Model.extra = {'filtering': filtering, 'ordering': ordering}
            DYNAMIC_MODEL_REGISTRY[self.slug] = Model

        return DYNAMIC_MODEL_REGISTRY[self.slug]


class Link(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    url = models.URLField(max_length=2000, null=False, blank=False)

    def __str__(self):
        domain = urlparse(self.url).netloc
        return f'{self.title} ({domain})'


class Version(models.Model):
    collected_at = models.DateField(null=False, blank=False)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    download_url = models.URLField(max_length=2000, null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    order = models.PositiveIntegerField(null=False, blank=False)

    def __str__(self):
        return f'{self.dataset.slug}.{self.name} (order: {self.order})'


class Table(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    default = models.BooleanField(null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    options = JSONField(null=True, blank=True)
    ordering = ArrayField(models.CharField(max_length=63),
                          null=False, blank=False)
    filtering = ArrayField(models.CharField(max_length=63),
                           null=True, blank=True)
    version = models.ForeignKey(Version, on_delete=models.CASCADE,
                                null=False, blank=False)


    def __str__(self):
        return f'{self.dataset.slug}.{self.version.name}.{self.name}'


class Field(models.Model):
    TYPES = ['binary', 'bool', 'date', 'datetime', 'decimal', 'email',
             'float', 'integer', 'json', 'percent', 'text',]
    TYPE_CHOICES = [(value, value) for value in TYPES]

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    null = models.BooleanField(null=False, blank=True, default=True)
    name = models.CharField(max_length=63)
    options = JSONField(null=True, blank=True)
    show = models.BooleanField(null=False, blank=True, default=True)
    table = models.ForeignKey(Table, on_delete=models.CASCADE,
                              null=False, blank=False)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES,
                            null=False, blank=False)
    version = models.ForeignKey(Version, on_delete=models.CASCADE,
                                null=True, blank=True)

    def __str__(self):
        return (f'{self.dataset.slug}.{self.version.name}.{self.table.name}'
                f'.{self.name}')

    @property
    def field_class(self):
        field_types = {
            'date': models.DateField,
            'datetime': models.DateTimeField,
            'decimal': models.DecimalField,
            'integer': models.IntegerField,
            'string': models.CharField,
        }
        kwargs = self.options or {}
        kwargs['null'] = self.null
        return field_types[self.type](**kwargs)
