import hashlib
from collections import OrderedDict
from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.test import TestCase
from model_bakery import baker, seq
from rows import fields

from core.dynamic_models import DynamicModelMixin
from core.models import Dataset, DataTable, Field, Table, TableFile, Version
from core.tests.utils import BaseTestCaseWithSampleDataset
from utils.file_info import human_readable_size


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


class FieldModelTests(TestCase):
    def test_searchable_queryset(self):
        field = baker.make(Field, searchable=True)
        baker.make(Field, searchable=False)

        qs = Field.objects.searchable()

        assert field in qs
        assert 1 == qs.count()

    def test_frontend_filters(self):
        field = baker.make(Field, frontend_filter=True)
        baker.make(Field, frontend_filter=False)

        qs = Field.objects.frontend_filters()

        assert field in qs
        assert 1 == qs.count()

    def test_choiceables_queryset(self):
        field = baker.make(Field, frontend_filter=True, has_choices=True)
        baker.make(Field, frontend_filter=True, has_choices=False)
        baker.make(Field, frontend_filter=False)

        qs = Field.objects.choiceables()

        assert field in qs
        assert 1 == qs.count()


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

    def test_deactivate_does_not_handle_activation_by_default(self):
        old_data_table = DataTable.new_data_table(self.table)
        old_data_table.activate()
        new_data_table = DataTable.new_data_table(self.table)
        new_data_table.activate()

        new_data_table.deactivate()
        old_data_table.refresh_from_db()
        new_data_table.refresh_from_db()

        assert old_data_table.active is False
        assert new_data_table.active is False

    def test_deactivate_activates_most_recent_if_flag(self):
        oldest_data_table = DataTable.new_data_table(self.table)
        oldest_data_table.activate()
        old_data_table = DataTable.new_data_table(self.table)
        old_data_table.activate()
        new_data_table = DataTable.new_data_table(self.table)
        new_data_table.activate()

        new_data_table.deactivate(activate_most_recent=True)
        oldest_data_table.refresh_from_db()
        old_data_table.refresh_from_db()
        new_data_table.refresh_from_db()

        assert oldest_data_table.active is False
        assert new_data_table.active is False
        assert old_data_table.active is True


class DatasetModelTests(TestCase):
    def setUp(self):
        self.dataset = baker.make(Dataset)
        self.version = baker.make(Version, dataset=self.dataset)
        self.tables = baker.make(Table, dataset=self.dataset, version=self.version, _quantity=2)

    def test_property_list_dataset_table_most_recent_fiels_sorted_by_name(self):
        table_1, table_2 = self.tables
        baker.make(TableFile, filename="sample_01.csv", table=table_1)  # old table file
        new_table_1_file = baker.make(TableFile, filename="sample_02.csv", table=table_1)
        baker.make(TableFile, filename="csv_data_01.csv", table=table_2)  # old table file
        new_table_2_file = baker.make(TableFile, filename="csv_data_02.csv", table=table_2)

        table_files = self.dataset.tables_files

        assert 2 == len(table_files)
        assert new_table_2_file == table_files[0]
        assert new_table_1_file == table_files[1]

    def test_raise_exception_if_no_table_file_for_a_table(self):
        baker.make(TableFile, filename="sample_02.csv", table=self.tables[0])  # only one table with file
        with pytest.raises(TableFile.DoesNotExist):
            self.dataset.tables_files

    def test_property_to_organize_sha512sums_from_the_dataset_table_files(self):
        table_file_1 = baker.make(TableFile, filename="sample_02.csv", table=self.tables[0])
        table_file_2 = baker.make(TableFile, filename="csv_data_02.csv", table=self.tables[1])

        hasher = hashlib.sha512()
        expected_content = ""
        for table_file in [table_file_2, table_file_1]:
            hasher.update(expected_content.encode())
            expected_content += f"{table_file.sha512sum}  {table_file.filename}\n"
        expected_url = f"{settings.AWS_S3_ENDPOINT_URL}{settings.MINIO_STORAGE_DATASETS_BUCKET_NAME}/{self.dataset.slug}/{settings.MINIO_DATASET_SHA512SUMS_FILENAME}"

        sha512sums = self.dataset.sha512sums
        assert settings.MINIO_DATASET_SHA512SUMS_FILENAME == sha512sums.filename
        assert expected_content == sha512sums.content
        assert hasher.hexdigest() == sha512sums.sha512sum
        assert expected_url == sha512sums.file_url
        assert human_readable_size(len(expected_content.encode())) == sha512sums.readable_size

    def test_property_to_list_all_files_from_a_dataset(self):
        baker.make(TableFile, filename="sample_02.csv", table=self.tables[0])
        baker.make(TableFile, filename="csv_data_02.csv", table=self.tables[1])

        expected_files = self.dataset.tables_files + [self.dataset.sha512sums]

        assert expected_files == self.dataset.all_files

    def test_return_empty_list_if_no_visible_table(self):
        baker.make(TableFile, filename="sample_02.csv", table=self.tables[0])
        baker.make(TableFile, filename="csv_data_02.csv", table=self.tables[1])
        Table.objects.all().update(hidden=True)

        assert [] == self.dataset.all_files


class DynamicTableModelTest(BaseTestCaseWithSampleDataset):
    DATASET_SLUG = "sample"
    TABLE_NAME = "sample_table"
    FIELDS_KWARGS = [
        {
            "name": "sample_field",
            "options": {"max_length": 10},
            "type": "text",
            "null": False,
            "filtering": True,
            "choices": {"data": ["foo", "bar"]},
        },
        {
            "name": "obfuscated_field",
            "options": {"max_length": 10},
            "type": "text",
            "null": False,
            "filtering": True,
            "choices": {},
            "obfuscate": True,
        },
    ]

    def test_filter_by_obfuscate_exact_value(self):
        value = "123456"
        entry = baker.make(self.TableModel, obfuscated_field=value)
        baker.make(self.TableModel, obfuscated_field="other")

        query = {"obfuscated_field": value}
        qs = self.TableModel.objects.apply_filters(query)

        assert 1 == qs.count()
        assert entry in qs

    def test_filter_by_obfuscate_partial_value(self):
        value = "123456"
        entry = baker.make(self.TableModel, obfuscated_field=value)
        baker.make(self.TableModel, obfuscated_field="other")

        query = {"obfuscated_field": "**34**"}
        qs = self.TableModel.objects.apply_filters(query)

        assert 1 == qs.count()
        assert entry in qs
