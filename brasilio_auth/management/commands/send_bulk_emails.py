import rows
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
        parser.add_argument("-d", "--dry-run", default=False, action="store_true")

    def handle(self, *args, **kwargs):
        input_filename = kwargs["input_filename"]
        table = rows.import_from_csv(input_filename)
        template_obj = self.load_email_template(kwargs["email_template"])

        for row in table:
            context = Context(row._asdict())
            rendered_template = template_obj.render(context=context)
            send_email(
                subject="Subject",
                body=rendered_template,
                from_email="from@example.com",
                to=["to@example.com"],
            )
