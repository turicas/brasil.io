from unittest.mock import Mock, patch

from captcha.fields import ReCaptchaField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.template.loader import get_template
from django.test import TestCase, override_settings
from django.urls import reverse

from brasilio_auth.models import NewsletterSubscriber
from brasilio_auth.views import ActivationView
from traffic_control.tests.util import TrafficControlClient

User = get_user_model()


@patch.object(ReCaptchaField, "validate", Mock(return_value=True))
class UserCreationViewTests(TestCase):
    client_class = TrafficControlClient

    def setUp(self):
        self.url = reverse("brasilio_auth:sign_up")
        passwd = "someverygoodpassword"
        self.data = {
            "username": "foo",
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
            "captcha": "captcha-code",
        }

    def test_render_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "brasilio_auth/user_creation_form.html")
        assert "form" in response.context

    def test_render_form_errors_if_invalid_post(self):
        response = self.client.post(self.url, data={})
        self.assertTemplateUsed(response, "brasilio_auth/user_creation_form.html")
        assert bool(response.context["form"].errors) is True

    def test_create_inactive_user_and_redirect_to_sign_up_complete(self):
        assert len(mail.outbox) == 0
        assert 1 == User.objects.count()  # auto import covid 19 user
        assert User.objects.filter(username=settings.COVID19_AUTO_IMPORT_USER).exists()

        response = self.client.post(self.url, data=self.data)
        user = User.objects.get(username="foo")

        assert not user.is_active
        assert len(mail.outbox) == 1
        self.assertRedirects(response, reverse("brasilio_auth:sign_up_complete"))
        assert not NewsletterSubscriber.objects.exists()

    def test_create_user_as_newsletter_subscriber(self):
        self.data["subscribe_newsletter"] = True

        self.client.post(self.url, data=self.data)

        user = User.objects.get(username="foo")
        assert not user.is_active
        assert NewsletterSubscriber.objects.filter(user=user).exists()

    @override_settings(REGISTRATION_OPEN=False)
    def test_redirect_to_not_allowed_if_closed_subscription(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("brasilio_auth:sign_up_disallowed"))

    def test_form_error_if_trying_to_create_user_with_existing_username(self):
        response = self.client.post(self.url, data=self.data)
        assert User.objects.filter(username="foo").exists()

        self.data["username"] = "FOO"
        self.data["email"] = "new@foo.com"
        response = self.client.post(self.url, data=self.data)
        self.assertTemplateUsed(response, "brasilio_auth/user_creation_form.html")
        print(response.context["form"].errors)
        assert bool(response.context["form"].errors) is True


class ActivationViewTests(TestCase):
    def test_attributes_configuration(self):
        assert reverse("brasilio_auth:activation_complete") == ActivationView.success_url
        assert "brasilio_auth/activation_failed.html" == ActivationView.template_name
        assert get_template(ActivationView.template_name)
