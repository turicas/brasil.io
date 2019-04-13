from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.test import TestCase

from brasilio_auth.forms import UserCreationForm
from brasilio_auth.models import NewsletterSubscriber


class UserCreationFormTests(TestCase):

    def test_required_fields(self):
        required_fields = ['username', 'email', 'password1', 'password2']

        form = UserCreationForm({})
        self.assertFalse(form.is_valid())

        for required in required_fields:
            self.assertIn(required, form.errors)
        self.assertEqual(len(required_fields), len(form.errors))
        assert issubclass(UserCreationForm, DjangoUserCreationForm)

    def test_create_user(self):
        passwd = 'qweasdzxc42'
        data = {
            'username': 'foo',
            'email': 'foo@bar.com',
            'password1': passwd,
            'password2': passwd,
        }

        form = UserCreationForm(data)
        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertEqual(data['username'], user.username)
        self.assertEqual(data['email'], user.email)
        self.assertTrue(user.check_password(passwd))
        self.assertFalse(NewsletterSubscriber.objects.filter(user=user).exists())

    def test_subscribe_to_newsleter(self):
        data = {
            'username': 'foo',
            'email': 'foo@bar.com',
            'password1': '123123asd',
            'password2': '123123asd',
            'subscribe_newsletter': True,
        }

        form = UserCreationForm(data)
        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertTrue(NewsletterSubscriber.objects.filter(user=user).exists())
