from unittest.mock import Mock, patch

from captcha.fields import ReCaptchaField
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.test import TestCase, override_settings
from model_bakery import baker

from brasilio_auth.forms import TokenApiManagementForm, UserCreationForm
from brasilio_auth.models import NewsletterSubscriber


class UserCreationFormTests(TestCase):
    username_invalid_error = "Nome de usuário pode conter apenas letras, números e '_' e não deve ser um documento"
    username_max_length_error = "Certifique-se de que o valor tenha no máximo 150 caracteres (ele possui 151)."
    username_exists_error = "Nome de usuário já existente (escolha um diferente)."

    def test_required_fields(self):
        required_fields = ["username", "email", "password1", "password2", "captcha"]

        form = UserCreationForm({})
        assert form.is_valid() is False

        for required in required_fields:
            assert required in form.errors
        assert len(required_fields) == len(form.errors)
        assert issubclass(UserCreationForm, DjangoUserCreationForm)

    @patch.object(ReCaptchaField, "validate", Mock(return_value=True))
    def test_create_user(self):
        passwd = "verygoodpassword"
        data = {
            "username": "foo",
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
            "captcha": "captcha-validation",
        }

        form = UserCreationForm(data)
        assert form.is_valid() is True
        user = form.save()

        assert data["username"] == user.username
        assert data["email"] == user.email
        assert user.check_password(passwd) is True
        assert not NewsletterSubscriber.objects.filter(user=user).exists()

    @patch.object(ReCaptchaField, "validate", Mock(return_value=True))
    def test_respect_abstract_user_max_length_for_username(self):
        passwd = "verygoodpassword"
        data = {
            "username": "a" * 150,
            "email": "another_foo@bar.com",
            "password1": passwd,
            "password2": passwd,
            "captcha": "captcha-validation",
        }

        form = UserCreationForm(data)
        assert form.is_valid()

        data["username"] = "a" * 151
        form = UserCreationForm(data)
        assert not form.is_valid()
        assert "username" in form.errors
        assert "email" not in form.errors
        assert form.errors["username"] == [self.username_max_length_error]

    @patch.object(ReCaptchaField, "validate", Mock(return_value=True))
    def test_invalid_username_if_already_exists(self):
        baker.make(settings.AUTH_USER_MODEL, username="foo")
        passwd = "verygoodpassword"
        data = {
            "username": "foo",
            "email": "another_foo@bar.com",
            "password1": passwd,
            "password2": passwd,
            "captcha": "captcha-validation",
        }

        form = UserCreationForm(data)
        assert form.is_valid() is False
        assert "username" in form.errors
        assert "email" not in form.errors
        assert form.errors["username"] == [self.username_exists_error]

    @patch.object(ReCaptchaField, "validate", Mock(return_value=True))
    def test_invalid_email_if_user_already_exists(self):
        baker.make(settings.AUTH_USER_MODEL, email="foo@bar.com", username="foo")
        passwd = "verygoodpassword"
        data = {
            "username": "another_foo",
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
            "captcha": "captcha-validation",
        }

        form = UserCreationForm(data)
        assert not form.is_valid()
        assert "email" in form.errors
        assert "username" not in form.errors

    @patch.object(ReCaptchaField, "validate", Mock(return_value=True))
    def test_email_validation_does_not_break_if_different_letter_case(self):
        baker.make(settings.AUTH_USER_MODEL, email="foo@bar.com", username="foo")
        passwd = "verygoodpassword"
        data = {
            "username": "another_foo",
            "email": "FOO@bar.com",
            "password1": passwd,
            "password2": passwd,
            "captcha": "captcha-validation",
        }

        form = UserCreationForm(data)
        assert not form.is_valid()
        assert "email" in form.errors
        assert "username" not in form.errors

    def test_do_not_validate_if_bad_captcha(self):
        passwd = "verygoodpassword"
        data = {
            "username": "foo",
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
            "captcha": "invalid-captcha",
        }

        form = UserCreationForm(data)

        assert not form.is_valid()
        assert "captcha" in form.errors

    @patch.object(ReCaptchaField, "validate", Mock(return_value=True))
    def test_invalid_username_characters(self):
        passwd = "verygoodpassword"
        data = {
            "username": "foo@",
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
            "captcha": "captcha-validation",
        }

        form = UserCreationForm(data)
        assert not form.is_valid()
        assert "username" in form.errors
        assert form.errors["username"] == [self.username_invalid_error]

    @patch.object(ReCaptchaField, "validate", Mock(return_value=True))
    def test_invalid_username_digits(self):
        passwd = "verygoodpassword"
        data = {
            "username": "123.456.789-01",
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
            "captcha": "captcha-validation",
        }

        form = UserCreationForm(data)
        assert not form.is_valid()
        assert "username" in form.errors
        assert form.errors["username"] == [self.username_invalid_error]

    @patch.object(ReCaptchaField, "validate", Mock(return_value=True))
    def test_do_not_set_username_to_lowercase(self):
        passwd = "verygoodpassword"
        username = "Foo"
        data = {
            "username": username,
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
            "captcha": "captcha-validation",
        }

        form = UserCreationForm(data)
        assert form.is_valid()
        assert form.cleaned_data["username"] == username

    @patch.object(ReCaptchaField, "validate", Mock(return_value=True))
    def test_strip_and_force_lowercase_email(self):
        passwd = "verygoodpassword"
        username = "Foo"
        data = {
            "username": username,
            "email": "FOO@bar.com ",
            "password1": passwd,
            "password2": passwd,
            "captcha": "captcha-validation",
        }

        form = UserCreationForm(data)
        expected_email = "foo@bar.com"
        assert form.is_valid()
        assert form.cleaned_data["email"] == expected_email


class TestTokenApiManagementForm(TestCase):
    def test_required_fields(self):
        required_fields = ["captcha"]

        form = TokenApiManagementForm({})
        assert not form.is_valid()

        assert len(form.errors) == len(required_fields)
        assert all([f in form.errors for f in required_fields])

    @override_settings(DISABLE_RECAPTCHA=True)
    def test_captcha_validades_if_disabled(self):
        form = TokenApiManagementForm({"captcha": "foo"})
        assert form.is_valid(), form.errors
