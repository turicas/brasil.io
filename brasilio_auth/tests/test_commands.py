from tempfile import NamedTemporaryFile

import pytest
from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import TestCase


class TestSendBulkEmails(TestCase):
    def setUp(self):
        self.input_file = NamedTemporaryFile(suffix=".csv")
        self.email_template = NamedTemporaryFile(suffix=".txt")

        with open(self.input_file.name, "w") as fobj:
            fobj.write(
                "nome,data,to_email,subject\nnome_1,data_1,email_1,subject_1\n"
                "nome_2,data_2,email_2,subject_2"
            )

        with open(self.email_template.name, "w") as fobj:
            fobj.write("Enviado para {{ nome }} em {{ data }}")

        self.input_file.seek(0)
        self.email_template.seek(0)

        self.expexted_send_email = [
            {
                "body": "Enviado para nome_1 em data_1",
                "subject": "subject_1",
                "to": ["email_1"],
                "from_email": settings.DEFAULT_FROM_EMAIL,
            },
            {
                "body": "Enviado para nome_2 em data_2",
                "subject": "subject_2",
                "to": ["email_2"],
                "from_email": settings.DEFAULT_FROM_EMAIL,
            }
        ]

    def assert_sent_email_metadata(self, email, metadata):
        for key, value in metadata.items():
            assert email.__getattribute__(key) == value

    def test_send_bulk_emails(self):
        call_command("send_bulk_emails", self.input_file.name, self.email_template.name)

        assert len(mail.outbox) == 2
        self.assert_sent_email_metadata(mail.outbox[0], self.expexted_send_email[0])
        self.assert_sent_email_metadata(mail.outbox[1], self.expexted_send_email[1])

    def test_send_email_custom_from_email(self):
        kwargs = {"from": "Example Email <email@example.com>"}
        call_command(
            "send_bulk_emails",
            self.input_file.name,
            self.email_template.name,
            **kwargs
        )

        self.expexted_send_email[0]["from_email"] = kwargs["from"]
        self.expexted_send_email[1]["from_email"] = kwargs["from"]

        assert len(mail.outbox) == 2
        self.assert_sent_email_metadata(mail.outbox[0], self.expexted_send_email[0])
        self.assert_sent_email_metadata(mail.outbox[1], self.expexted_send_email[1])

    def test_assert_mandatory_fields(self):
        with open(self.input_file.name, "w") as fobj:
            fobj.write("nome,data\nnome_1,data_1\nnome_2,data_2")

        self.input_file.seek(0)
        with pytest.raises(AssertionError):
            call_command("send_bulk_emails", self.input_file.name, self.email_template.name)

    def test_do_not_send_mail(self):
        call_command(
            "send_bulk_emails",
            self.input_file.name,
            self.email_template.name,
            "--dry-run"
        )

        assert len(mail.outbox) == 0
