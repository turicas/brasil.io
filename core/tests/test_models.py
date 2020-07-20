from collections import OrderedDict
from unittest.mock import Mock, patch

from django.test import TestCase
from model_bakery import baker, seq
from rows import fields

from core.models import DataTable, DynamicModelMixin, Table


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


class DataTableModelTests(TestCase):
    def setUp(self):
        self.table = baker.make(Table, dataset__slug="ds-slug", name="table_name")

    def test_new_datatable_with_table_name_suffix(self):
        data_table = DataTable.new_data_table(self.table)
        splited_name = data_table.db_table_name.split("_")

        assert not data_table.id  # creates an instance but doesn't save it in the DB
        assert data_table.table == self.table
        assert data_table.active is False
        assert len(splited_name) == 4  # data + ds slug + table + suffix
        assert splited_name[0] == "data"
        assert splited_name[1] == "dsslug"
        assert splited_name[2] == "tablename"
        assert len(splited_name[3]) == 8  # suffix with 8 chars

    def test_new_datatable_without_table_name_suffix(self):
        data_table = DataTable.new_data_table(self.table, suffix_size=0)
        splited_name = data_table.db_table_name.split("_")

        assert not data_table.id  # creates an instance but doesn't save it in the DB
        assert data_table.table == self.table
        assert data_table.active is False
        assert len(splited_name) == 3  # data + ds slug + table
        assert splited_name[0] == "data"
        assert splited_name[1] == "dsslug"
        assert splited_name[2] == "tablename"

    def test_activate_data_table(self):
        data_table = DataTable.new_data_table(self.table)

        data_table.activate()
        data_table.refresh_from_db()

        assert data_table.active is True

    @patch.object(Table, "get_model", Mock())
    def test_activate_data_table_updates_previous_active_as_inactive(self):
        old_data_table = DataTable.new_data_table(self.table)
        old_data_table.activate()

        new_data_table = DataTable.new_data_table(self.table)
        new_data_table.activate()

        old_data_table.refresh_from_db()
        new_data_table.refresh_from_db()

        assert old_data_table.active is False
        assert new_data_table.active is True
        assert self.table.get_model.called is False

    @patch.object(Table, "get_model", Mock(DynamicModelMixin))
    def test_activate_data_table_updates_previous_active_as_inactive_and_delete_table_if_flagged(self):
        old_data_table = DataTable.new_data_table(self.table)
        old_data_table.activate()

        new_data_table = DataTable.new_data_table(self.table)
        new_data_table.activate(drop_inactive_table=True)

        old_data_table.refresh_from_db()
        new_data_table.refresh_from_db()

        assert old_data_table.active is False
        assert new_data_table.active is True
        self.table.get_model.assert_called_once_with(cache=False, data_table=old_data_table)
        Model = self.table.get_model(cache=False, data_table=old_data_table)
        Model.delete_table.assert_called_once_with()
