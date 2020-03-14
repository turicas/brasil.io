from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.test import TestCase

from brasilio_auth.forms import UserCreationForm
from brasilio_auth.models import NewsletterSubscriber


class UserCreationFormTests(TestCase):

    def test_required_fields(self):
        required_fields = ['username', 'email', 'password1', 'password2']

        form = UserCreationForm({})
        assert form.is_valid() is False

        for required in required_fields:
            assert required in form.errors
        assert len(required_fields) == len(form.errors)
        assert issubclass(UserCreationForm, DjangoUserCreationForm)

    def test_create_user(self):
        passwd = 'someverygoodpassword'
        data = {
            'username': 'foo',
            'email': 'foo@bar.com',
            'password1': passwd,
            'password2': passwd,
        }

        form = UserCreationForm(data)
        assert form.is_valid() is True
        user = form.save()

        assert data['username'] == user.username
        assert data['email'] == user.email
        assert user.check_password(passwd) is True
        assert not NewsletterSubscriber.objects.filter(user=user).exists()

    def test_subscribe_to_newsleter(self):
        data = {
            'username': 'foo',
            'email': 'foo@bar.com',
            'password1': '123123asd',
            'password2': '123123asd',
            'subscribe_newsletter': True,
        }

        form = UserCreationForm(data)
        assert form.is_valid() is True
        user = form.save()

        assert NewsletterSubscriber.objects.filter(user=user).exists()
