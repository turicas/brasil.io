import os
import time
from collections import OrderedDict

from django.db import transaction
from django.db.utils import ProgrammingError
from django.utils import timezone
from rows.utils import ProgressBar, open_compressed, pgimport

from core.models import Table


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
        if self.flag_import_data:
            self.import_data(filename)

    def import_data(self, filename):
        # Create the table if not exists
        Model = self.table.get_model()
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
