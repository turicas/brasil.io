from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from model_bakery import baker

from brasilio_auth.models import NewsletterSubscriber, NormalizedEmail

User = get_user_model()


class NewsletterSubscriberQuerySetTests(TestCase):
    def test_active_queryset_filter(self):
        active = baker.make(NewsletterSubscriber, user__is_active=True)
        baker.make(NewsletterSubscriber, user__is_active=False)

        active_only = NewsletterSubscriber.objects.active()
        assert 2 == NewsletterSubscriber.objects.count()
        assert active in active_only
        assert 1 == active_only.count()


class NormalizedEmailTests(TestCase):
    def test_normalized_email_eh_criado_no_save_do_user(self):
        user = baker.make(User, email="Foo.Bar+spam@GoogleMail.com")
        assert "foobar@gmail.com" == user.normalized_email.value

    def test_normalized_email_eh_atualizado_quando_email_do_user_muda(self):
        user = baker.make(User, email="primeiro@gmail.com")
        user.email = "segundo@gmail.com"
        user.save()
        assert 1 == NormalizedEmail.objects.filter(user=user).count()
        assert "segundo@gmail.com" == NormalizedEmail.objects.get(user=user).value

    def test_normalized_email_nao_eh_recriado_quando_save_nao_muda_email(self):
        user = baker.make(User, email="constante@gmail.com")
        pk_original = user.normalized_email.pk
        user.save()
        assert pk_original == NormalizedEmail.objects.get(user=user).pk

    def test_value_eh_unico_no_banco(self):
        primeiro = baker.make(User, email="")
        segundo = baker.make(User, email="")
        NormalizedEmail.objects.create(user=primeiro, value="colidente@gmail.com")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NormalizedEmail.objects.create(user=segundo, value="colidente@gmail.com")
