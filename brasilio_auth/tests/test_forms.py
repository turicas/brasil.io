from model_bakery import baker

from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.conf import settings
from django.test import TestCase

from brasilio_auth.forms import UserCreationForm
from brasilio_auth.models import NewsletterSubscriber


class UserCreationFormTests(TestCase):
    def test_required_fields(self):
        required_fields = ["username", "email", "password1", "password2"]

        form = UserCreationForm({})
        assert form.is_valid() is False

        for required in required_fields:
            assert required in form.errors
        assert len(required_fields) == len(form.errors)
        assert issubclass(UserCreationForm, DjangoUserCreationForm)

    def test_create_user(self):
        passwd = "verygoodpassword"
        data = {
            "username": "foo",
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
        }

        form = UserCreationForm(data)
        assert form.is_valid() is True
        user = form.save()

        assert data["username"] == user.username
        assert data["email"] == user.email
        assert user.check_password(passwd) is True
        assert not NewsletterSubscriber.objects.filter(user=user).exists()

    def test_subscribe_to_newsleter(self):
        data = {
            "username": "foo",
            "email": "foo@bar.com",
            "password1": "123123asd",
            "password2": "123123asd",
            "subscribe_newsletter": True,
        }

        form = UserCreationForm(data)
        assert form.is_valid() is True
        user = form.save()

        assert NewsletterSubscriber.objects.filter(user=user).exists()

    def test_force_lower_for_username(self):
        passwd = "verygoodpassword"
        data = {
            "username": "FOO",
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
        }

        form = UserCreationForm(data)
        assert form.is_valid() is True
        user = form.save()
        user.refresh_from_db()

        assert "foo" == user.username

    def test_respect_abstract_user_max_length_for_username(self):
        passwd = "verygoodpassword"
        data = {
            "username": "a" * 150,
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
        }

        form = UserCreationForm(data)
        assert form.is_valid()

        data["username"] = "a" * 151
        form = UserCreationForm(data)
        assert not form.is_valid()
        assert "username" in form.errors

    def test_invalid_username_if_already_exists(self):
        baker.make(settings.AUTH_USER_MODEL, username="foo")
        passwd = "verygoodpassword"
        data = {
            "username": "foo",
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
        }

        form = UserCreationForm(data)
        assert form.is_valid() is False
        assert "username" in form.errors

    def test_invalid_email_if_user_already_exists(self):
        baker.make(settings.AUTH_USER_MODEL, email="foo@bar.com")
        passwd = "verygoodpassword"
        data = {
            "username": "foo",
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
        }

        form = UserCreationForm(data)
        assert not form.is_valid()
        assert "email" in form.errors

    def test_email_validation_does_not_break_if_different_letter_case(self):
        baker.make(settings.AUTH_USER_MODEL, email="foo@bar.com")
        passwd = "verygoodpassword"
        data = {
            "username": "foo",
            "email": "FOO@bar.com",
            "password1": passwd,
            "password2": passwd,
        }

        form = UserCreationForm(data)
        assert not form.is_valid()
        assert "email" in form.errors
