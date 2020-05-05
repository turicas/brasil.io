from collections import OrderedDict
from model_bakery import baker, seq
from rows import fields

from django.test import TestCase

from core.models import Table


class TableModelTests(TestCase):
    def test_schema_as_ordered_dict(self):
        table = baker.make(Table)
        fields = baker.make(
            "core.Field", table=table, name=seq("field_"), dataset=table.dataset, order=seq(1), _quantity=10,
        )

        assert isinstance(table.schema, OrderedDict)
        field_names = list(table.schema.keys())
        for i, field in enumerate(fields):
            assert field.name == field_names[i]

    def test_schema_fields_types(self):
        db_fields_to_rows_fields = {
            "binary": fields.BinaryField,
            "bool": fields.BoolField,
            "date": fields.DateField,
            "datetime": fields.DatetimeField,
            "decimal": fields.DecimalField,
            "email": fields.EmailField,
            "float": fields.FloatField,
            "integer": fields.IntegerField,
            "json": fields.JSONField,
            "string": fields.TextField,
            "text": fields.TextField,
        }

        table = baker.make(Table)
        field = baker.prepare("core.Field", table=table, name="table_column", dataset=table.dataset)

        for db_field_type, rows_field_type in db_fields_to_rows_fields.items():
            field.type = db_field_type
            field.save()
            table.refresh_from_db()

            assert rows_field_type == table.schema["table_column"]

    def test_table_default_manager_excludes_hidden_tables(self):
        dataset = baker.make("core.Dataset")
        table = baker.make(Table, dataset=dataset, default=True)
        hidden_table = baker.make(Table, hidden=True, dataset=dataset, default=True)

        tables = Table.objects.all()
        assert 1 == tables.count()
        assert table in tables
        assert hidden_table not in tables

        tables = dataset.table_set.all()
        assert 1 == tables.count()
        assert table in tables
        assert hidden_table not in tables

        assert table == Table.objects.for_dataset(dataset).default()
        assert table == Table.objects.named(table.name)

        tables = Table.with_hidden.all()
        assert 2 == tables.count()
        assert table in tables
        assert hidden_table in tables

        tables = Table.with_hidden.for_dataset(dataset)
        assert 2 == tables.count()
        assert table in tables
        assert hidden_table in tables
