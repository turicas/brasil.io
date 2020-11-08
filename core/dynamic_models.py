from textwrap import dedent

import django.contrib.postgres.indexes as pg_indexes
import django.db.models.indexes as django_indexes
from django.db import connection, models

FIELD_TYPES = {
    "binary": models.BinaryField,
    "bool": models.BooleanField,  # TODO: rename to "boolean"
    "date": models.DateField,
    "datetime": models.DateTimeField,
    "decimal": models.DecimalField,
    "email": models.EmailField,
    "float": models.FloatField,
    "integer": models.IntegerField,
    "json": models.JSONField,
    "string": models.CharField,  # TODO: rename to "char"
    "text": models.TextField,
}
# TODO: since FIELD_TYPES is only used internally by Brasil.IO, we may delete
# it from dynamic_models and use only internally on Dataset model creation.


class DynamicModelMixin:
    """Default mixin to be used on dynamic models, contains database operations"""

    @classmethod
    def create_table(cls, indexes=True):
        model_indexes = cls._meta.indexes
        if not indexes:
            cls._meta.indexes = []
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(cls)
        except Exception:
            raise
        finally:
            # TODO: check if this approach really works - it looks like Django
            # is caching something so the model class must be recreated - see
            # Table.get_model comments.
            cls._meta.indexes = model_indexes

    @classmethod
    def create_indexes(cls):
        with connection.cursor() as cursor:
            for index in cls._meta.indexes:
                index_class = type(index)
                if index_class is django_indexes.Index:
                    index_type = "btree"
                elif index_class is pg_indexes.GinIndex:
                    index_type = "gin"
                else:
                    raise ValueError("Cannot identify index type of {index}")

                fieldnames = []
                for fieldname in index.fields:
                    if fieldname.startswith("-"):
                        value = f"{fieldname[1:]} DESC"
                    else:
                        value = f"{fieldname} ASC"
                    if index_type == "gin":
                        value = value.split(" ")[0]
                    fieldnames.append(value)

                fieldnames = ",\n                            ".join(fieldnames)
                query = dedent(
                    f"""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS {index.name}
                        ON {cls.tablename()} USING {index_type} (
                            {fieldnames}
                        );
                """
                ).strip()
                cursor.execute(query)

    @classmethod
    def delete_table(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(cls)


def create_model_class(name, module, fields, mixins=None, meta=None, managers=None):
    """
    Create a Django Model class dynamically

    name: new model's name
    module: module which the model will be attached to.
            Example: "myapp.models"
    mixins: list of mixin classes to inject on model class (first has higher
            priority). Models created with this function will inherit at list
            from `dynamic_models.DynamicModelMixin` and
            `django.db.models.Model`.
    meta: dict with objects inside model's Meta internal class.
          Example:
              {
                  "db_table": "mytablename",
                  "ordering": ["created_at", "name"],
                  "indexes": [models.Index(name="idx_mytable_ordering", fields=["created_at", "name"])]
              }
    managers: dict with manager classes.
              Example:
                  {
                      "objects": MyQuerySet.as_manager()
                  }
    """

    # TODO: use app instead of module (so we use the same pattern as Django)
    # TODO: may use registry from django.apps.registry.App instead of local
    # dict

    if meta is None:
        meta = {}

    parent_classes = [models.Model, DynamicModelMixin]
    if mixins is not None:
        parent_classes.extend(mixins)
    parent_classes = tuple(reversed(parent_classes))

    if managers is None:
        managers = {}

    Options = type("Meta", (object,), meta)
    Model = type(name, parent_classes, {"__module__": module, "Meta": Options, **managers, **fields,},)

    # TODO: may create a model proxy (injecting mixins) and then return the
    # proxy
    return Model


def model_source_code(Model):
    meta = Model._meta
    model_name = Model.__name__
    ordering = meta.get("ordering", [])
    indexes = ",\n                    ".join(
        f"models.{index.__class__.__name__}(name={repr(index.name)}, fields={repr(index.fields)})"
        for index in meta.indexes
    )
    fields_text = []
    for field in meta.fields:
        if field.name == "id":
            continue
        field_type = field.__class__.__name__.replace("Field", "").lower()
        if field_type == "searchvector":
            field_class = "SearchVector"
        elif field_type == "jsonfield":
            field_class = "JSONField"
        else:
            if field_type == "char":
                field_type = "string"
            field_class = "models." + FIELD_TYPES[field_type].__name__
        kwargs = {
            "null": field.null,
        }
        options = "max_length max_digits decimal_places".split()
        for option in options:
            value = getattr(field, option, None)
            if value:
                kwargs[option] = value
        field_args = ", ".join("{}={}".format(key, repr(value)) for key, value in kwargs.items())
        fields_text.append(f"{field.name} = {field_class}({field_args})")

    fields = "\n            ".join(fields_text)
    # TODO: missing objects?
    # TODO: add all meta possible key/values
    return dedent(
        f"""
        class {model_name}(models.Model):

            {fields}

            class Meta:
                indexes = [
                    {indexes}
                ]
                ordering = {repr(ordering)}
    """
    ).strip()
