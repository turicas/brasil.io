from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserCreationViewTests(TestCase):

    def setUp(self):
        self.url = reverse('brasilio_auth:sign_up')

        passwd = 'someverygoodpassword'
        self.data = {
            'username': 'foo',
            'email': 'foo@bar.com',
            'password1': passwd,
            'password2': passwd,
        }

    def test_render_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'brasilio_auth/user_creation_form.html')
        self.assertTrue('form' in response.context)

    def test_render_form_errors_if_invalid_post(self):
        response = self.client.post(self.url, data={})
        self.assertTemplateUsed(response, 'brasilio_auth/user_creation_form.html')
        self.assertTrue(bool(response.context['form'].errors))

    def test_create_and_login_with_user(self):
        self.assertEqual(0, User.objects.count())

        response = self.client.post(self.url, data=self.data)
        user = User.objects.get(username='foo')

        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL, fetch_redirect_response=False)
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(str(user.pk), self.client.session['_auth_user_id'])
