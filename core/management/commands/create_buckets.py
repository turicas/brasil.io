from django.conf import settings
from django.core.management.base import BaseCommand

from project.storage import storage


class Command(BaseCommand):
    help = "Create base buckets"

    def handle(self, *args, **kwargs):
        buckets = storage.buckets()
        for bucket in (settings.AWS_S3_DATASETS_BUCKET_NAME, settings.AWS_STORAGE_BUCKET_NAME):
            if bucket in buckets:
                continue
            storage.create_bucket(bucket)
