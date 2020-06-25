from pathlib import Path
import datetime
import rows

from django.core.management.base import BaseCommand
from django.core.validators import URLValidator

from covid19.models import DailyBulletin


class Command(BaseCommand):
    help = "Update/create daily Covid19 bulletin"

    def add_arguments(self, parser):
        parser.add_argument('date', type=str, help="Date in format YYYY-MM-DD")
        parser.add_argument('image_url', type=str, help="Bulletin image URL")
        parser.add_argument("--csv", type=Path, help="CSV file to update the bulletin JSON field")

    def clean_args(self, **kwargs):
        date, image_url, csv_file = kwargs['date'], kwargs['image_url'], kwargs['csv']
        date = datetime.date(*[int(n) for n in date.split('-')])
        url_validator = URLValidator()
        url_validator(image_url)
        if csv_file and not csv_file.exists():
            raise Exception(f"The CSV {csv_file} does not exists")

        return date, image_url, csv_file


    def handle(self, *args, **kwargs):
        date, image_url, csv_file = self.clean_args(**kwargs)

        json_data = []
        if csv_file:
            json_data = [r._asdict() for r in rows.import_from_csv(csv_file)]

        print(f"Atualizando imagem do boletim {date} para {image_url}")

        defaults = {"image_url": image_url}
        if json_data:
            defaults['detailed_data'] = json_data
        bulletin, _ = DailyBulletin.objects.update_or_create(date=date, defaults=defaults)

        print(f"Atualizado com sucesso: {bulletin.admin_url}")
