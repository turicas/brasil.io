import os
import csv
import rows

from django.core.management.base import BaseCommand
from pathlib import Path

from django.contrib.auth import get_user_model
from clipping.models import Clipping


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("csv", type=Path, help="CSV file to update the clippings JSON field")

    def clean_args(self, **kwargs):
        csv_file = kwargs["csv"]
        if csv_file and not csv_file.exists():
            raise Exception(f"The CSV {csv_file} does not exists")
        return csv_file

    def handle(self, *args, **kwargs):
        csv_file = self.clean_args(**kwargs)
        username = "turicas"
        user = get_user_model().objects.get(username=username)
        with open(csv_file, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                p = Clipping(date=row['data'], vehicle=row['veiculo'], author=row['autor'], title=row['titulo'],
                             category=row['categoria'], url=row['link'], published=True, added_by=user)
                p.save()
        self.stdout.write(self.style.SUCCESS('Successfully imported'))
