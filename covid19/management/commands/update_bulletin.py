import datetime

from django.core.management.base import BaseCommand
from django.core.validators import URLValidator

from covid19.models import DailyBulletin


class Command(BaseCommand):
    help = "Update/create daily Covid19 bulletin"

    def add_arguments(self, parser):
        parser.add_argument('date', type=str, help="Date in format YYYY-MM-DD")
        parser.add_argument('image_url', type=str, help="Bulletin image URL")

    def handle(self, *args, **kwargs):
        date, image_url = kwargs['date'], kwargs['image_url']
        date = datetime.date(*[int(n) for n in date.split('-')])
        url_validator = URLValidator()
        url_validator(image_url)

        print(f"Atualizando imagem do boletim {date} para {image_url}")

        bulletin, _ = DailyBulletin.objects.update_or_create(date=date, defaults={"image_url": image_url})

        print(f"Atualizado com sucesso: {bulletin.admin_url}")
