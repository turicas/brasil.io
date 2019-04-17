from model_mommy import mommy

from django.test import TestCase
from django.contrib.auth import get_user_model

from brasilio_auth.models import NewsletterSubscriber
from brasilio_auth.services import subscribers_as_csv_rows


User = get_user_model()

class TestSubscribersAsCSVRows(TestCase):

    def setUp(self):
        users = mommy.make(
            User,
            _quantity=5,
            _fill_optional=True
        )
        self.subscribers = [mommy.make(NewsletterSubscriber, user=u) for u in users]

    def test_get_csv_rows(self):
        rows = subscribers_as_csv_rows()

        assert len(rows) == len(self.subscribers) + 1
        assert ('name', 'email') == rows[0]

        for user in [s.user for s in self.subscribers]:
            assert (user.get_full_name(), user.email) in rows

    def test_get_csv_rows_without_header(self):
        rows = subscribers_as_csv_rows(include_header=False)

        assert len(rows) == len(self.subscribers)
        for user in [s.user for s in self.subscribers]:
            assert (user.get_full_name(), user.email) in rows
