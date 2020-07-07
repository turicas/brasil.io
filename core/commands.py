import os
import time
from collections import OrderedDict

from django.core.cache import cache
from django.db import transaction, connection
from django.db.utils import ProgrammingError
from django.utils import timezone
from rows.utils import ProgressBar, open_compressed, pgimport

from core.models import Field, Table


class ImportDataCommand:
    def __init__(self, table, **options):
        self.table = table
        self.flag_import_data = options["import_data"]
        self.flag_vacuum = options["vacuum"]
        self.flag_clear_view_cache = options["clear_view_cache"]
        self.flag_create_filter_indexes = options["create_filter_indexes"]
        self.flag_fill_choices = options["fill_choices"]
        self.collect_date = options["collect_date"]

    @classmethod
    def execute(cls, dataset_slug, tablename, filename, **options):
        table = Table.with_hidden.for_dataset(dataset_slug).named(tablename)
        self = cls(table, **options)
        db_table_suffix = '_temp'

        if self.flag_import_data:
            Model = self.table.get_model(cache=False, db_table_suffix=db_table_suffix)
            self.import_data(filename, Model)
            self.replace_model(TargetModel=self.table.get_model(cache=False), TempModel=Model)
            Model = self.table.get_model(cache=False)
        else:
            Model = self.table.get_model(cache=False)
        if self.flag_vacuum:
            self.run_vacuum(Model)
        if self.flag_create_filter_indexes:
            self.create_filter_indexes(Model)
        if self.flag_fill_choices:
            self.fill_choices(Model)
        if self.flag_clear_view_cache:
            print("Clearing view cache...")
            cache.clear()

    def import_data(self, filename, Model):
        # Create the table if not exists
        with transaction.atomic():
            try:
                Model.delete_table()
            except ProgrammingError:  # Does not exist
                pass
            finally:
                Model.create_table(create_indexes=False)
                Model.create_triggers()

        # Get file object, header and set command to run
        table_name = Model._meta.db_table
        database_uri = os.environ["DATABASE_URL"]
        encoding = "utf-8"  # TODO: receive as a parameter
        timeout = 0.1  # TODO: receive as a parameter
        start_time = time.time()
        progress = ProgressBar(prefix="Importing data", unit="bytes")

        # TODO: change the way we do it (CSV dialect may change, encoding
        # etc.)
        file_header = open_compressed(filename).readline().strip().split(",")
        table_schema = self.table.schema
        schema = OrderedDict([(field_name, table_schema[field_name]) for field_name in file_header])
        try:
            import_meta = pgimport(
                filename=filename,
                encoding=encoding,
                dialect="excel",
                database_uri=database_uri,
                table_name=table_name,
                create_table=False,
                timeout=timeout,
                callback=progress.update,
                schema=schema,
            )
        except RuntimeError as exception:
            progress.close()
            print("ERROR: {}".format(exception.args[0]))
            exit(1)
        else:
            progress.close()
            self.table.import_date = timezone.now()
            self.table.save()
            if self.collect_date:
                self.table.version.collected_at = self.collect_date
                self.table.version.save()
            end_time = time.time()
            duration = end_time - start_time
            rows_imported = import_meta["rows_imported"]
            print(
                "  done in {:7.3f}s ({} rows imported, {:.3f} rows/s).".format(
                    duration, rows_imported, rows_imported / duration
                )
            )
        self.table.invalidate_cache()

    def replace_model(self, TargetModel, TempModel):
        table_name, temp_name = TargetModel._meta.db_table, TempModel._meta.db_table
        trigger_name, temp_trigger_name = TargetModel.get_trigger_name(), TempModel.get_trigger_name()
        seq_name, temp_seq_name = f'{table_name}_id_seq', f'{temp_name}_id_seq'
        with transaction.atomic():
            print("Replacing existing model by the new one...", end="", flush=True)
            start = time.time()
            try:
                TargetModel.delete_table()
            except ProgrammingError:  # Does not exist
                pass
            finally:
                with connection.schema_editor() as schema_editor:
                    schema_editor.alter_db_table(TempModel, temp_name, table_name)
                with connection.cursor() as cursor:
                    trigger_rename_sql = f"""
                        ALTER TRIGGER {temp_trigger_name} ON {table_name} RENAME TO {trigger_name};
                    """.strip()
                    cursor.execute(trigger_rename_sql)
                    seq_rename_sql = f"ALTER SEQUENCE {temp_seq_name} RENAME TO {seq_name}"
                    cursor.execute(seq_rename_sql)
            print("  done in {:.3f}s.".format(time.time() - start))

    def run_vacuum(self, Model):
        print("Running VACUUM ANALYSE...", end="", flush=True)
        start = time.time()
        Model.analyse_table()
        end = time.time()
        print("  done in {:.3f}s.".format(end - start))

    def create_filter_indexes(self, Model):
        # TODO: warn if field has_choices but not in Table.filtering
        print("Creating filter indexes...", end="", flush=True)
        start = time.time()
        Model.create_indexes()  # TODO: add "IF NOT EXISTS"
        end = time.time()
        print("  done in {:.3f}s.".format(end - start))

    def fill_choices(self, Model):
        print("Filling choices...")
        start = time.time()
        choiceables = Field.objects.for_table(self.table).choiceables()
        for field in choiceables:
            print("  {}".format(field.name), end="", flush=True)
            start_field = time.time()
            field.update_choices()
            field.save()
            end_field = time.time()
            print(" - done in {:.3f}s.".format(end_field - start_field))
        end = time.time()
        print("  done in {:.3f}s.".format(end - start))
