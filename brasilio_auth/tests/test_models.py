from django.test import TestCase
from model_bakery import baker

from brasilio_auth.models import NewsletterSubscriber


class NewsletterSubscriberQuerySetTests(TestCase):
    def test_active_queryset_filter(self):
        active = baker.make(NewsletterSubscriber, user__is_active=True)
        baker.make(NewsletterSubscriber, user__is_active=False)

        active_only = NewsletterSubscriber.objects.active()
        assert 2 == NewsletterSubscriber.objects.count()
        assert active in active_only
        assert 1 == active_only.count()
