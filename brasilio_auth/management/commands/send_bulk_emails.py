import django_rq
import rows
from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import Context, Template

from core.email import send_email


class Command(BaseCommand):
    def load_email_template(self, email_template):
        with open(email_template, "r") as fobj:
            return Template(fobj.read())

    def add_arguments(self, parser):
        parser.add_argument("input_filename")
        parser.add_argument("email_template")
        parser.add_argument("--from")
        parser.add_argument("-d", "--dry-run", default=False, action="store_true")

    def handle(self, *args, **kwargs):
        input_filename = kwargs["input_filename"]
        table = rows.import_from_csv(input_filename)
        error_msg = "Arquivo CSV deve conter campos 'to_email' e 'subject'"
        assert {"to_email", "subject"}.issubset(set(table.field_names)), error_msg

        template_obj = self.load_email_template(kwargs["email_template"])
        from_email = kwargs["from"] or settings.DEFAULT_FROM_EMAIL

        for row in table:
            context = Context(row._asdict())
            rendered_template = template_obj.render(context=context)
            if not kwargs["dry_run"]:
                django_rq.enqueue(
                    send_email,
                    subject=row.subject,
                    body=rendered_template,
                    from_email=from_email,
                    to=[row.to_email],
                )
            else:
                print(rendered_template)
