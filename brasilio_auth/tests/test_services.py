from django.contrib.auth import get_user_model
from django.test import TestCase
from model_bakery import baker

from brasilio_auth.models import NewsletterSubscriber
from brasilio_auth.services import subscribers_as_csv_rows

User = get_user_model()


class TestSubscribersAsCSVRows(TestCase):
    def setUp(self):
        users = baker.make(User, is_active=True, _quantity=5, _fill_optional=True)
        self.subscribers = [baker.make(NewsletterSubscriber, user=u) for u in users]

    def test_get_csv_rows(self):
        baker.make(NewsletterSubscriber, user__is_active=False, _quantity=5)  # inactive

        rows = subscribers_as_csv_rows()

        assert len(rows) == len(self.subscribers) + 1
        assert ("username", "email") == rows[0]

        for user in [s.user for s in self.subscribers]:
            assert (user.username, user.email) in rows

    def test_get_csv_rows_without_header(self):
        rows = subscribers_as_csv_rows(include_header=False)

        assert len(rows) == len(self.subscribers)
        for user in [s.user for s in self.subscribers]:
            assert (user.username, user.email) in rows
