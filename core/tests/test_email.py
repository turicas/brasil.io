from django.core import mail
from django.test import TestCase

from core.email import send_email


class TestSendEmail(TestCase):
    def test_send_emnail(self):
        subject = "Subject"
        body = "Body"
        from_email = "from@example.com"
        to = ["to@example.com"]
        reply_to = ["Reply To <replyto@example.com"]

        send_email(
            subject=subject,
            body=body,
            from_email=from_email,
            to=to,
            reply_to=reply_to,
        )
        assert len(mail.outbox) == 1
        assert body == mail.outbox[0].body
        assert subject == mail.outbox[0].subject
        assert from_email == mail.outbox[0].from_email
        assert to == mail.outbox[0].to
        assert reply_to == mail.outbox[0].reply_to
