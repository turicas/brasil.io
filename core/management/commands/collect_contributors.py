import json
from pathlib import Path

from django.core.management.base import BaseCommand

from core.util import brasilio_github_contributors


class Command(BaseCommand):
    help = "Update choices cache"

    def add_arguments(self, parser):
        parser.add_argument("output_filename")

    def handle(self, *args, **kwargs):
        output_filename = kwargs["output_filename"]

        data = brasilio_github_contributors()
        filename = Path(output_filename)
        if not filename.parent.exists():
            filename.parent.mkdir(parents=True)
        with open(filename, mode="w") as fobj:
            json.dump(data, fobj)
        print("Done! Now send the file:")
        print(f"    s3cmd put {filename} s3://meta/contribuidores.json")
