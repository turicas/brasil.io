import django_rq
import rows
from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import Context, Template
from tqdm import tqdm

from core.email import send_email


class Command(BaseCommand):
    def load_email_template(self, email_template):
        with open(email_template, "r") as fobj:
            return Template(fobj.read())

    def print_email_metadata(self, metadata):
        for key, value in metadata.items():
            print(f"{key}: {value}")

        print("-" * 80)

    def add_arguments(self, parser):
        parser.add_argument("--sender", default=settings.DEFAULT_FROM_EMAIL)
        parser.add_argument("--dry-run", default=False, action="store_true")
        parser.add_argument("--wait-time", default=15)
        parser.add_argument("input_filename")
        parser.add_argument("template_filename")

    def handle(self, *args, **kwargs):
        input_filename = kwargs["input_filename"]
        table = rows.import_from_csv(input_filename)
        error_msg = "Arquivo CSV deve conter campos 'to_email' e 'subject'"
        assert {"to_email", "subject"}.issubset(set(table.field_names)), error_msg

        template_obj = self.load_email_template(kwargs["template_filename"])
        wait_time = kwargs["wait_time"]
        from_email = kwargs["sender"]

        for row in tqdm(table):
            context = Context(row._asdict())
            rendered_template = template_obj.render(context=context)
            email_kwargs = {
                "subject": row.subject,
                "body": rendered_template,
                "from_email": from_email,
                "to": [row.to_email],
            }
            if not kwargs["dry_run"]:
                django_rq.enqueue(send_email, **email_kwargs)
            else:
                self.print_email_metadata(email_kwargs)
