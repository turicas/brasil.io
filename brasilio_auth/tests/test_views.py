from unittest.mock import Mock, patch

from captcha.fields import ReCaptchaField
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core import mail
from django.template.loader import get_template
from django.test import TestCase, override_settings
from django.urls import reverse
from model_bakery import baker

from brasilio_auth.forms import TokenApiManagementForm
from api.models import Token
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


class ManageApiTokensViewsTests(TestCase):
    client_class = TrafficControlClient

    def setUp(self):
        self.user = baker.make(get_user_model(), is_active=True)
        self.client.force_login(self.user)
        self.url = reverse("brasilio_auth:list_api_tokens")

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        redirect_url = f"{settings.LOGIN_URL}?next={self.url}"
        self.assertRedirects(response, redirect_url)

    def test_list_user_tokens(self):
        tokens = baker.make("api.Token", user=self.user, _quantity=5)
        baker.make("api.Token", _quantity=2)  # other users tokens

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "brasilio_auth/list_user_api_tokens.html")
        context = response.context
        assert 5 == len(context["tokens"])
        for token in tokens:
            assert token in context["tokens"]
        assert context["num_tokens_available"] == settings.MAX_NUM_API_TOKEN_PER_USER - 5


class CreateAPiTokensViewsTests(TestCase):
    client_class = TrafficControlClient

    def setUp(self):
        self.user = baker.make(get_user_model(), is_active=True)
        self.client.force_login(self.user)
        self.url = reverse("brasilio_auth:create_api_token")
        self.data = {"captcha": "foo"}

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        redirect_url = f"{settings.LOGIN_URL}?next={self.url}"
        self.assertRedirects(response, redirect_url)

    def test_render_valid_template_on_get(self):
        response = self.client.get(self.url)
        context = response.context
        assert 200 == response.status_code
        self.assertTemplateUsed(response, "brasilio_auth/new_api_token_form.html")
        assert isinstance(context["form"], TokenApiManagementForm)

    def test_do_not_create_api_token_if_invalid_post(self):
        response = self.client.post(self.url, data={})
        context = response.context
        self.assertTemplateUsed(response, "brasilio_auth/new_api_token_form.html")
        assert context["form"].errors
        assert not Token.objects.exists()

    @patch.object(TokenApiManagementForm, 'is_valid', Mock(return_value=True))
    def test_create_new_token_for_user(self):
        assert 0 == self.user.auth_tokens.count()

        response = self.client.post(self.url, self.data, follow=True)
        context = response.context
        new_token = self.user.auth_tokens.get()

        self.assertTemplateUsed(response, "brasilio_auth/list_user_api_tokens.html")
        assert 1 == len(context["tokens"])
        assert new_token in context["tokens"]
        assert context["num_tokens_available"] == settings.MAX_NUM_API_TOKEN_PER_USER - 1
        user_messages = list(context["messages"])
        assert len(user_messages) == 1
        msg = user_messages[0]
        assert messages.SUCCESS == msg.level
        assert f"Nova chave de API: <tt>{new_token}</tt>" == msg.message

    @patch.object(TokenApiManagementForm, 'is_valid', Mock(return_value=True))
    def test_display_error_message_if_user_has_max_num_of_tokens(self):
        baker.make("api.Token", user=self.user, _quantity=settings.MAX_NUM_API_TOKEN_PER_USER)
        tokens = self.user.auth_tokens.all()

        response = self.client.post(self.url, data=self.data, follow=True)
        context = response.context

        self.assertTemplateUsed(response, "brasilio_auth/list_user_api_tokens.html")
        assert settings.MAX_NUM_API_TOKEN_PER_USER == len(context["tokens"])
        for token in tokens:
            assert token in context["tokens"]
        assert context["num_tokens_available"] == 0
        user_messages = list(context["messages"])
        assert len(user_messages) == 1
        msg = user_messages[0]
        assert messages.ERROR == msg.level
        assert f"Você já possui número máximo de {settings.MAX_NUM_API_TOKEN_PER_USER} chaves de API." == msg.message


class DeleteApiTokenViewsTests(TestCase):
    client_class = TrafficControlClient

    def setUp(self):
        self.user = baker.make(get_user_model(), is_active=True)
        self.token = baker.make("api.Token", user=self.user)
        self.client.force_login(self.user)
        self.url = reverse("brasilio_auth:delete_api_token", args=[self.token.key])

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        redirect_url = f"{settings.LOGIN_URL}?next={self.url}"
        self.assertRedirects(response, redirect_url)

    def test_404_if_token_does_not_exist(self):
        self.token.delete()
        response = self.client.get(self.url)
        assert 404 == response.status_code

    def test_404_if_token_does_not_belong_to_logged_user(self):
        self.client.logout()
        self.client.force_login(baker.make(get_user_model(), is_active=True))
        response = self.client.get(self.url)
        assert 404 == response.status_code

    def test_delete_token(self):
        user_other_tokens = baker.make("api.Token", user=self.user, _quantity=3)
        assert 4 == self.user.auth_tokens.count()

        response = self.client.get(self.url, follow=True)
        context = response.context

        self.assertTemplateUsed(response, "brasilio_auth/list_user_api_tokens.html")
        assert 3 == len(context["tokens"]) == len(user_other_tokens)
        for token in user_other_tokens:
            assert token in context["tokens"]
        user_messages = list(context["messages"])
        assert len(user_messages) == 1
        msg = user_messages[0]
        assert messages.SUCCESS == msg.level
        assert "Chave de API deletada com sucesso." == msg.message
