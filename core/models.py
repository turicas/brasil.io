import hashlib
from textwrap import dedent
from urllib.parse import urlparse

import django.db.models.indexes as django_indexes
from django.contrib.postgres.fields import ArrayField, JSONField
import django.contrib.postgres.indexes as pg_indexes
from django.contrib.postgres.search import (SearchQuery, SearchVector,
                                            SearchVectorField)
from django.db import connection, models


DYNAMIC_MODEL_REGISTRY = {}
FIELD_TYPES = {
    'binary': models.BinaryField,
    'bool': models.BooleanField,
    'date': models.DateField,
    'datetime': models.DateTimeField,
    'decimal': models.DecimalField,
    'email': models.EmailField,
    'float': models.FloatField,
    'integer': models.IntegerField,
    'json': JSONField,
    'string': models.CharField,
    'text': models.TextField,
}

def model_to_code(Model):
    meta = Model._meta
    extra = Model.extra
    model_name = Model.__name__
    ordering = extra.get('ordering', [])
    filtering = extra.get('filtering', [])
    search = extra.get('search', [])
    indexes = ',\n                    '.join(
        f'models.{index.__class__.__name__}(name={repr(index.name)}, fields={repr(index.fields)})'
        for index in meta.indexes
    )
    fields_text = []
    for field in meta.fields:
        if field.name == 'id':
            continue
        field_type = field.__class__.__name__.replace('Field', '').lower()
        if field_type == 'searchvector':
            field_class = 'SearchVector'
        elif field_type == 'jsonfield':
            field_class = 'JSONField'
        else:
            if field_type == 'char':
                field_type = 'string'
            field_class = 'models.' + FIELD_TYPES[field_type].__name__
        kwargs = {
            'null': field.null,
        }
        options = 'max_length max_digits decimal_places'.split()
        for option in options:
            value = getattr(field, option, None)
            if value:
                kwargs[option] = value
        field_args = ', '.join(
            '{}={}'.format(key, repr(value)) for key, value in kwargs.items()
        )
        fields_text.append(
            f'{field.name} = {field_class}({field_args})'
        )

    fields = '\n            '.join(fields_text)
    # TODO: missing objects?
    return dedent(f'''
        class {model_name}(models.Model):

            {fields}

            class Meta:
                indexes = [
                    {indexes}
                ]
                ordering = {repr(ordering)}
    ''').strip()

def make_index_name(tablename, index_type, fields):
    idx_hash = hashlib.md5(
        f'{tablename} {index_type} {", ".join(sorted(fields))}'.encode('ascii')
    ).hexdigest()
    tablename = tablename.replace('data_', '').replace('-', '')[:12]
    return f'idx_{tablename}_{index_type[0]}{idx_hash[-12:]}'


class DynamicModelMixin:

    @classmethod
    def tablename(cls):
        return cls._meta.db_table

    @classmethod
    def create_table(cls, create_indexes=True):
        indexes = cls._meta.indexes
        if not create_indexes:
            cls._meta.indexes = []
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(cls)
        except:
            raise
        finally:
            # TODO: check if this approach really works - it looks like Django
            # is caching something so the model class must be recreated - see
            # Table.get_model comments.
            cls._meta.indexes = indexes

    @classmethod
    def analyse_table(cls):
        with connection.cursor() as cursor:
            cursor.execute('VACUUM ANALYSE {}'.format(cls.tablename()))

    @classmethod
    def create_triggers(cls):
        trigger_name = f'tgr_tsv_{cls.tablename()}'
        fieldnames = ', '.join(cls.extra['search'])
        query = dedent(f'''
            CREATE TRIGGER {trigger_name}
                BEFORE INSERT OR UPDATE
                ON {cls.tablename()}
                FOR EACH ROW EXECUTE PROCEDURE
                tsvector_update_trigger(search_data, 'pg_catalog.portuguese', {fieldnames})
        ''').strip()
        # TODO: replace pg_catalog.portuguese with dataset language
        with connection.cursor() as cursor:
            cursor.execute(query)

    @classmethod
    def create_indexes(cls):
        with connection.cursor() as cursor:
            for index in cls._meta.indexes:
                index_class = type(index)
                if index_class is django_indexes.Index:
                    index_type = 'btree'
                elif index_class is pg_indexes.GinIndex:
                    index_type = 'gin'
                else:
                    raise ValueError('Cannot identify index type of {index}')

                fieldnames = []
                for fieldname in index.fields:
                    if fieldname.startswith('-'):
                        value = f'{fieldname[1:]} DESC'
                    else:
                        value = f'{fieldname} ASC'
                    if index_type == 'gin':
                        value = value.split(' ')[0]
                    fieldnames.append(value)

                fieldnames = ',\n                            '.join(fieldnames)
                query = dedent(f'''
                    CREATE INDEX CONCURRENTLY {index.name}
                        ON {cls.tablename()} USING {index_type} (
                            {fieldnames}
                        );
                ''').strip()
                cursor.execute(query)

    @classmethod
    def delete_table(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(cls)


class DynamicModelQuerySet(models.QuerySet):

    def search(self, search_query):
        qs = self
        search_fields = self.model.extra['search']
        if search_query and search_fields:
            words = search_query.split()
            config = 'pg_catalog.portuguese'  # TODO: get from self.model.extra
            query = None
            for word in set(words):
                if not word:
                    continue
                if query is None:
                    query = SearchQuery(word, config=config)
                else:
                    query = query & SearchQuery(word, config=config)
            qs = qs.filter(search_data=query)
        return qs

    def apply_filters(self, filtering):
        qs = self
        model_filtering = self.model.extra['filtering']
        if model_filtering is not None:
            for field_name in model_filtering:
                value = filtering.get(field_name, None)
                if value == 'false':
                    value = False
                elif value == 'true':
                    value = True
                elif value is None:
                    value = True
                    field_name += '__isnull'
                qs = qs.filter(**{field_name: value})
        return qs

    def apply_ordering(self, query):
        qs = self
        model_ordering = self.model.extra['ordering']
        model_filtering = self.model.extra['filtering']
        allowed_fields = set(model_ordering + model_filtering)
        clean_allowed = [field.replace('-', '').strip().lower()
                         for field in allowed_fields]
        ordering_query = [field for field in query
                          if field.replace('-', '') in clean_allowed]
        if ordering_query:
            qs = qs.order_by(*ordering_query)
        elif model_ordering:
            qs = qs.order_by(*model_ordering)

        return qs

    def filter_by_querystring(self, querystring):
        queryset = self
        query = querystring.copy()
        order_by = query.pop('order-by', [''])
        order_by = [field.strip().lower()
                    for field in order_by[0].split(',')
                    if field.strip()]
        search_query = query.pop('search', [''])[0]
        query = {key: value for key, value in query.items() if value}
        if search_query:
            queryset = queryset.search(search_query)
        if query:
            queryset = queryset.apply_filters(query)
        queryset = queryset.apply_ordering(order_by)

        return queryset

    def count(self):
        if getattr(self, '_count', None) is not None:
            return self._count

        query = self.query
        if not query.where:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT reltuples FROM pg_class WHERE relname = %s",
                        [query.model._meta.db_table],
                    )
                    self._count = int(cursor.fetchone()[0])
            except:
                self._count = super().count()
        else:
            self._count = super().count()

        return self._count


class Dataset(models.Model):
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
        return self.table_set.filter(version=version).order_by('name')

    @property
    def last_version(self):
        return self.get_last_version()

    def get_table(self, tablename):
        return Table.objects.for_dataset(self).named(tablename)

    def get_default_table(self):
        return Table.objects.for_dataset(self).default()

    def __str__(self):
        return ('{} (by {}, source: {})'
                .format(self.name, self.author_name, self.source_name))

    def get_model_declaration(self):
        version = self.version_set.order_by('order').last()
        table = self.table_set.get(version=version, default=True)
        return table.get_model_declaration()

    def get_last_version(self):
        return self.version_set.order_by('order').last()


class Link(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    url = models.URLField(max_length=2000, null=False, blank=False)

    def __str__(self):
        domain = urlparse(self.url).netloc
        return '{} ({})'.format(self.title, domain)


class Version(models.Model):
    collected_at = models.DateField(null=False, blank=False)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    download_url = models.URLField(max_length=2000, null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    order = models.PositiveIntegerField(null=False, blank=False)

    def __str__(self):
        return ('{}.{} (order: {})'
                .format(self.dataset.slug, self.name, self.order))


class TableQuerySet(models.QuerySet):

    def for_dataset(self, dataset):
        if isinstance(dataset, str):
            kwargs = {'dataset__slug': dataset}
        else:
            kwargs = {'dataset': dataset}
        return self.filter(**kwargs)

    def default(self):
        return self.get(default=True)

    def named(self, name):
        return self.get(name=name)


class Table(models.Model):
    objects = TableQuerySet.as_manager()

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    default = models.BooleanField(null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    options = JSONField(null=True, blank=True)
    ordering = ArrayField(models.CharField(max_length=63),
                          null=False, blank=False)
    filtering = ArrayField(models.CharField(max_length=63),
                           null=True, blank=True)
    search = ArrayField(models.CharField(max_length=63),
                        null=True, blank=True)
    version = models.ForeignKey(Version, on_delete=models.CASCADE,
                                null=False, blank=False)
    import_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return ('{}.{}.{}'.
                format(self.dataset.slug, self.version.name, self.name))

    @property
    def db_table(self):
        return 'data_{}_{}'.format(
            self.dataset.slug.replace('-', ''),
            self.name.replace('_', ''),
        )

    @property
    def fields(self):
        return self.field_set.all()

    def get_model(self, cache=True):
        if cache and self.id in DYNAMIC_MODEL_REGISTRY:
            return DYNAMIC_MODEL_REGISTRY[self.id]

        # TODO: unregister the model in Django if already registered (self.id
        # in DYNAMIC_MODEL_REGISTRY and not cache)
        # TODO: may use Django's internal registry instead of
        # DYNAMIC_MODEL_REGISTRY
        name = self.dataset.slug + '-' + self.name.replace('_', '-')
        model_name = ''.join([word.capitalize() for word in name.split('-')])
        fields = {field.name: field.field_class
                  for field in self.fields}
        fields['search_data'] = SearchVectorField(null=True)
        ordering = self.ordering or []
        filtering = self.filtering or []
        search = self.search or []
        indexes = []
        # TODO: add has_choices fields also
        if ordering:
            indexes.append(
                django_indexes.Index(
                    name=make_index_name(name, 'order', ordering),
                    fields=ordering,
                )
            )
        if filtering:
            for field_name in filtering:
                if ordering == [field_name]:
                    continue
                indexes.append(
                    django_indexes.Index(
                        name=make_index_name(name, 'filter', [field_name]),
                        fields=[field_name]
                    )
                )
        if search:
            indexes.append(
                pg_indexes.GinIndex(
                    name=make_index_name(name, 'search', ['search_data']),
                    fields=['search_data']
                )
            )

        Options = type(
            'Meta',
            (object,),
            {
                'ordering': ordering,
                'indexes': indexes,
                'db_table': self.db_table,
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
        Model.extra = {
            'filtering': filtering,
            'ordering': ordering,
            'search': search,
        }
        DYNAMIC_MODEL_REGISTRY[self.id] = Model
        return Model

    def get_model_declaration(self):
        Model = self.get_model()
        return model_to_code(Model)


class FieldQuerySet(models.QuerySet):

    def for_table(self, table):
        return self.filter(table=table)

    def choiceables(self):
        return self.filter(has_choices=True, frontend_filter=True)


class Field(models.Model):
    objects = FieldQuerySet.as_manager()

    TYPE_CHOICES = [(value, value) for value in FIELD_TYPES.keys()]

    choices = JSONField(null=True, blank=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    frontend_filter = models.BooleanField(null=False, blank=True, default=False)
    has_choices = models.BooleanField(null=False, blank=True, default=False)
    link_template = models.TextField(max_length=2000, null=True, blank=True)
    order = models.PositiveIntegerField(null=False, blank=False)
    null = models.BooleanField(null=False, blank=True, default=True)
    name = models.CharField(max_length=63)
    options = JSONField(null=True, blank=True)
    obfuscate = models.BooleanField(null=False, blank=True, default=False)
    show = models.BooleanField(null=False, blank=True, default=True)
    show_on_frontend = models.BooleanField(null=False, blank=True, default=False)
    table = models.ForeignKey(Table, on_delete=models.CASCADE,
                              null=False, blank=False)
    title = models.CharField(max_length=63)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES,
                            null=False, blank=False)
    version = models.ForeignKey(Version, on_delete=models.CASCADE,
                                null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        options = self.options or {}
        options_str = ', '.join('{}={}'.format(key, repr(value))
                                               for key, value in options.items())
        return '{}.{}({})'.format(self.table.name, self.name, options_str)

    @property
    def field_class(self):
        kwargs = self.options or {}
        kwargs['null'] = self.null
        return FIELD_TYPES[self.type](**kwargs)

    def options_text(self):
        if not self.options:
            return ''

        return ', '.join(['{}={}'.format(key, repr(value))
                          for key, value in self.options.items()])

    def update_choices(self):
        Model = self.table.get_model()
        choices = Model.objects.order_by(self.name)\
                               .distinct(self.name)\
                               .values_list(self.name, flat=True)
        self.choices = {'data': [str(value) for value in choices]}
