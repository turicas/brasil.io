from django.contrib.auth import get_user_model
from django.test import TestCase

from brasilio_auth.models import NormalizedEmail

User = get_user_model()


class UserLoginViewTests(TestCase):
    def setUp(self):
        self.username = "testuser"
        self.email = "test@example.com"
        self.password = "supersecret"
        self.user = self.create_user(
            username=self.username,
            password=self.password,
            email=self.email,
        )

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

    def test_can_log_in_with_gmail_alias(self):
        self.create_user(username="gmailuser", email="user@gmail.com", password=self.password)
        assert self.login("u.s.e.r+tag@gmail.com", self.password)

    def test_can_log_in_with_googlemail_domain(self):
        self.create_user(username="gmuser", email="someone@gmail.com", password=self.password)
        assert self.login("someone@googlemail.com", self.password)

    def test_falls_back_to_raw_email_without_normalized_email(self):
        user = self.create_user(username="skipped", email="skip@example.com", password=self.password)
        NormalizedEmail.objects.filter(user=user).delete()
        assert self.login("skip@example.com", self.password)

    def test_user_in_normalized_email_collision_logs_in_with_own_email(self):
        self.create_user(username="primeiro", email="user@gmail.com", password="senha-do-primeiro")
        segundo = self.create_user(username="segundo", email="u.ser@gmail.com", password="senha-do-segundo")
        assert not NormalizedEmail.objects.filter(user=segundo).exists()
        assert self.login("u.ser@gmail.com", "senha-do-segundo")
        assert self.login("u.ser@gmail.com", "senha-do-primeiro")  # alias do primeiro continua valendo
        assert not self.login("u.ser@gmail.com", "senha-errada")

    def test_users_with_identical_email_log_in_by_their_own_password(self):
        self.create_user(username="antiga", email="dup@example.com", password="senha-antiga")
        self.create_user(username="nova", email="dup@example.com", password="senha-nova")
        assert self.login("dup@example.com", "senha-antiga")
        assert self.login("dup@example.com", "senha-nova")
        assert not self.login("dup@example.com", "senha-errada")
