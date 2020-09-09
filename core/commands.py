import csv
import hashlib
import math
import mimetypes
import os
import time
from collections import OrderedDict, namedtuple
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import requests
import rows
from cached_property import cached_property
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.utils import ProgrammingError
from django.template.loader import get_template
from django.utils import timezone
from minio import Minio
from tqdm import tqdm

from core.models import Dataset, DataTable, Field, Table, TableFile
from utils.file_info import human_readable_size
from utils.minio import MinioProgress


class ImportDataCommand:
    def __init__(self, table, **options):
        self.table = table
        self.flag_import_data = options["import_data"]
        self.flag_vacuum = options["vacuum"]
        self.flag_clear_view_cache = options["clear_view_cache"]
        self.flag_create_filter_indexes = options["create_filter_indexes"]
        self.flag_fill_choices = options["fill_choices"]
        self.flag_delete_old_table = options["delete_old_table"]
        self.collect_date = options["collect_date"]

    def log(self, msg, *args, **kwargs):
        print(msg, *args, **kwargs)

    @classmethod
    def execute(cls, dataset_slug, tablename, filename, **options):
        table = Table.with_hidden.for_dataset(dataset_slug).named(tablename)
        self = cls(table, **options)
        data_table = DataTable.new_data_table(table)  # in memory instance, not persisted in the DB

        if self.flag_import_data:
            self.log(f"Importing data to new table {data_table.db_table_name}")
            Model = self.table.get_model(cache=False, data_table=data_table)
            self.import_data(filename, Model)
        else:
            Model = self.table.get_model(cache=False)

        # Vaccum and concurrent index creation cannot run inside a transaction block
        if self.flag_vacuum:
            self.run_vacuum(Model)
        if self.flag_create_filter_indexes:
            self.create_filter_indexes(Model)

        try:
            with transaction.atomic():
                if self.flag_fill_choices:
                    self.fill_choices(Model)
                if self.flag_import_data:
                    table.data_table.deactivate(drop_table=self.flag_delete_old_table)
                    data_table.activate()
        except Exception as e:
            self.log(f"Deleting import table {data_table.db_table_name} due to an error.")
            data_table.delete_data_table()
            raise e

        if self.flag_clear_view_cache:
            self.log("Clearing view cache...")
            cache.clear()

    def import_data(self, filename, Model):
        # Create the table if not exists
        with transaction.atomic():
            try:
                Model.delete_table()
            except ProgrammingError:  # Does not exist
                pass
            finally:
                Model.create_table(indexes=False)
                Model.create_triggers()

        # Get file object, header and set command to run
        table_name = Model._meta.db_table
        database_uri = os.environ["DATABASE_URL"]
        encoding = "utf-8"  # TODO: receive as a parameter
        timeout = 0.1  # TODO: receive as a parameter
        start_time = time.time()
        progress = rows.utils.ProgressBar(prefix="Importing data", unit="bytes")

        sample_size = 1 * 1024 * 1024  # 1 MiB
        with rows.utils.open_compressed(filename, mode="rb") as fobj:
            sample = fobj.read(sample_size)
            dialect = rows.plugins.csv.discover_dialect(sample, encoding)
        with rows.utils.open_compressed(filename) as fobj:
            reader = csv.DictReader(fobj, dialect=dialect)
            file_header = reader.fieldnames
        table_schema = self.table.schema
        schema = OrderedDict([(field_name, table_schema[field_name]) for field_name in file_header])
        try:
            import_meta = rows.utils.pgimport(
                filename=filename,
                encoding=encoding,
                dialect=dialect,
                database_uri=database_uri,
                table_name=table_name,
                create_table=False,
                timeout=timeout,
                callback=progress.update,
                schema=schema,
            )
        except RuntimeError as exception:
            progress.close()
            Model.delete_table()
            self.log("ERROR: {}".format(exception.args[0]))
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
            self.log(
                "  done in {:7.3f}s ({} rows imported, {:.3f} rows/s).".format(
                    duration, rows_imported, rows_imported / duration
                )
            )
        self.table.invalidate_cache()

    def run_vacuum(self, Model):
        self.log("Running VACUUM ANALYSE...", end="", flush=True)
        start = time.time()
        Model.analyse_table()
        end = time.time()
        self.log("  done in {:.3f}s.".format(end - start))

    def create_filter_indexes(self, Model):
        # TODO: warn if field has_choices but not in Table.filtering
        self.log("Creating filter indexes...", end="", flush=True)
        start = time.time()
        Model.create_indexes()  # TODO: add "IF NOT EXISTS"
        end = time.time()
        self.log("  done in {:.3f}s.".format(end - start))

    def fill_choices(self, Model):
        self.log("Filling choices...")
        start = time.time()
        choiceables = Field.objects.for_table(self.table).choiceables()
        for field in choiceables:
            self.log("  {}".format(field.name), end="", flush=True)
            start_field = time.time()
            field.update_choices()
            field.save()
            end_field = time.time()
            self.log(" - done in {:.3f}s.".format(end_field - start_field))
        end = time.time()
        self.log("  done in {:.3f}s.".format(end - start))


class UpdateTableFileCommand:
    def __init__(self, table, file_url, **options):
        self.table = table
        self.file_url = file_url
        self.file_url_info = urlparse(file_url)
        self.hasher = hashlib.sha512()
        self.file_size = 0

        minio_endpoint = urlparse(settings.AWS_S3_ENDPOINT_URL).netloc
        self.should_upload = minio_endpoint != self.file_url_info.netloc
        self.minio = Minio(
            minio_endpoint, access_key=settings.AWS_ACCESS_KEY_ID, secret_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self._output_file = None
        self.delete_source = options["delete_source"]

    @property
    def output_file(self):
        if not self._output_file:
            self._output_file = NamedTemporaryFile(delete=False)
        return self._output_file

    def read_file_chunks(self, chunk_size):
        response = requests.get(self.file_url, stream=True)
        num_chunks = (
            math.ceil(int(response.headers["Content-Length"]) / chunk_size)
            if response.headers.get("Content-Length")
            else None
        )

        chunks = response.iter_content(chunk_size=chunk_size)

        for chunk in tqdm(chunks, desc=f"Downloading {self.file_url} chunks...", total=num_chunks):
            self.file_size += len(chunk)
            self.hasher.update(chunk)
            yield chunk

    def process_file_chunk(self, chunk, chunk_size):
        if self.should_upload:
            self.output_file.write(chunk)

    def finish_process(self):
        source = self.file_url_info.path  # /BUCKET_NAME/OBJ_PATH
        suffix = "".join(Path(source).suffixes)
        dest_name = f"{self.table.dataset.slug}/{self.table.name}{suffix}"
        bucket = settings.MINIO_STORAGE_DATASETS_BUCKET_NAME
        is_same_file = source == f"/{bucket}/{dest_name}"

        if self.should_upload:
            self.output_file.close()
            progress = MinioProgress()
            self.log(f"Uploading file to bucket: {bucket}")

            content_type, encoding = mimetypes.guess_type(dest_name)
            if encoding == "gzip":
                # quando é '.csv.gz' o retorno de guess_type é ('text/csv', 'gzip')
                content_type = "application/gzip"
            elif encoding is None:
                content_type = "text/plain"

            self.minio.fput_object(
                bucket, dest_name, self.output_file.name, progress=progress, content_type=content_type
            )
        elif not is_same_file:
            self.log(f"Copying {source} to bucket {bucket}")
            self.minio.copy_object(bucket, dest_name, source)
            if self.delete_source:
                self.log(f"Deleting {source}")
                split_source = source.split("/")
                source_bucket, source_obj = split_source[1], "/".join(split_source[2:])
                self.minio.remove_object(source_bucket, source_obj)
        else:
            self.log(f"Using {source} as the dataset file.", end="")

        os.remove(self.output_file.name)
        return f"{settings.AWS_S3_ENDPOINT_URL}{bucket}/{dest_name}"

    @classmethod
    def execute(cls, dataset_slug, tablename, file_url, **options):
        table = Table.with_hidden.for_dataset(dataset_slug).named(tablename)
        self = cls(table, file_url, **options)

        chunk_size = settings.MINIO_DATASET_DOWNLOAD_CHUNK_SIZE
        for chunk in self.read_file_chunks(chunk_size):
            self.process_file_chunk(chunk, chunk_size)

        new_file_url = self.finish_process()
        table_file, created = self.create_table_file(new_file_url)

        table_file_url = f"https://{settings.APP_HOST}{table_file.admin_url}"
        if created:
            self.log(f"\nNew TableFile entry: {table_file_url}")
        else:
            self.log(f"\nUsing existing TableFile entry: {table_file_url}")

        self.log(f"File hash: {table_file.sha512sum}")
        self.log(f"File size: {table_file.readable_size}")

    def create_table_file(self, file_url):
        filename = Path(urlparse(file_url).path).name
        table_file, created = TableFile.objects.get_or_create(
            table=self.table,
            file_url=file_url,
            sha512sum=self.hasher.hexdigest(),
            size=str(self.file_size),
            filename=filename,
        )
        return table_file, created

    def log(self, msg, *args, **kwargs):
        print(msg, *args, **kwargs)


class UpdateTableFileListCommand:
    FileListInfo = namedtuple("FileListInfo", ("filename", "file_url", "readable_size", "sha512sum"))

    def __init__(self, dataset, **options):
        self.dataset = dataset
        self.tables = dataset.tables
        minio_endpoint = urlparse(settings.AWS_S3_ENDPOINT_URL).netloc
        self.bucket = settings.MINIO_STORAGE_DATASETS_BUCKET_NAME
        self.minio = Minio(
            minio_endpoint, access_key=settings.AWS_ACCESS_KEY_ID, secret_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self._collect_date = options["collect_date"]

    @cached_property
    def all_table_files(self):
        return sorted([TableFile.objects.get_most_recent_for_table(t) for t in self.tables], key=lambda f: f.filename)

    @property
    def collect_date(self):
        return self._collect_date or max([t.collect_date for t in self.tables])

    def update_sha512_sums_file(self):
        temp_file = NamedTemporaryFile(delete=False, mode="w")
        fname = "SHA512SUMS"
        dest_name = f"{self.dataset.slug}/{fname}"

        sha_sum = hashlib.sha512()
        size = 0
        for table_file in self.all_table_files:
            content = f"{table_file.sha512sum}  {table_file.filename}\n"
            temp_file.write(content)
            sha_sum.update(content.encode())
            size += len(content.encode())
        temp_file.close()

        self.log(f"Uploading {fname}...")
        progress = MinioProgress()
        self.minio.fput_object(self.bucket, dest_name, temp_file.name, progress=progress, content_type="text/plain")

        file_info = self.FileListInfo(
            filename=fname,
            readable_size=human_readable_size(size),
            sha512sum=sha_sum.hexdigest(),
            file_url=f"{settings.AWS_S3_ENDPOINT_URL}{self.bucket}/{dest_name}",
        )
        os.remove(temp_file.name)

        return file_info

    def update_list_html(self, files_list):
        context = {
            "dataset": self.dataset,
            "capture_date": self.collect_date,
            "file_list": files_list,
        }
        list_template = get_template("tables_files_list.html")
        content = list_template.render(context=context)

        temp_file = NamedTemporaryFile(delete=False, mode="w")
        temp_file.write(content)
        temp_file.close()

        self.log("\nUploading list HTML...")
        dest_name = f"{self.dataset.slug}/_meta/list.html"
        progress = MinioProgress()
        self.minio.fput_object(
            self.bucket, dest_name, temp_file.name, progress=progress, content_type="text/html; charset=utf-8"
        )

        os.remove(temp_file.name)
        return f"{settings.AWS_S3_ENDPOINT_URL}{self.bucket}/{dest_name}"

    @classmethod
    def execute(cls, dataset_slug, **options):
        dataset = Dataset.objects.get(slug=dataset_slug)
        self = cls(dataset, **options)

        self.log(f"Starting to update {dataset_slug} dataset list files...")
        file_info = self.update_sha512_sums_file()
        url = self.update_list_html(self.all_table_files + [file_info])

        self.log(f"\nNew list html in {url}")

    def log(self, *args, **kwargs):
        print(*args, **kwargs)
