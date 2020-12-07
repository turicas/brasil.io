from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserLoginViewTests(TestCase):
    def setUp(self):
        self.username = "testuser"
        self.email = "test@example.com"
        self.password = "supersecret"
        self.user = self.create_user(username=self.username, password=self.password, email=self.email,)

    def create_user(self, username, password, email):
        user = User.objects.create(username=username, email=email, is_active=True)
        user.set_password(password)
        user.save()
        return user

    def login(self, username, password):
        return self.client.login(username=username, password=password)

    def test_can_log_in_with_username(self):
        assert self.login(self.username, self.password)

    def test_can_log_in_with_email(self):
        assert self.login(self.email, self.password)

    def test_try_to_hijack_user(self):
        username = self.email
        email = "cracker@example.com"
        password = "cr4ck3r"

        self.create_user(username=username, email=email, password=password)
        assert not self.login(username, password)
        assert self.login(email, password)
