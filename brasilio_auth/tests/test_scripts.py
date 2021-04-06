from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from model_bakery import baker

from api.models import Token
from brasilio_auth.models import NewsletterSubscriber
from brasilio_auth.scripts.migrate_wrong_usernames import migrate_usernames, possible_usernames
from brasilio_auth.scripts.migrate_duplicate_emails import run as run_migrate_duplicate_emails
from covid19.models import StateSpreadsheet

User = get_user_model()


class TestPossibleUsernames(TestCase):
    def test_username_equal_to_email(self):
        username = "test@example.com"
        email = "test@example.com"

        possible_values = possible_usernames(username, email, n_suffix=2)
        expected = ("test", "test", "test_example", "test_1")

        assert possible_values == expected

    def test_username_with_invalid_char_at_the_beginning(self):
        username = "@test"
        email = "test@example.com"

        possible_values = possible_usernames(username, email, n_suffix=2)
        expected = ("test", "test", "test_example", "test_1")

        assert possible_values == expected

    def test_username_with_invalid_char_at_the_end(self):
        username = "test@"
        email = "test@example.com"

        possible_values = possible_usernames(username, email, n_suffix=2)
        expected = ("test", "test", "test_example", "test_1")

        assert possible_values == expected

    def test_username_with_invalid_char_at_the_both_ends(self):
        username = "@test@"
        email = "test@example.com"

        possible_values = possible_usernames(username, email, n_suffix=2)
        expected = ("test", "test", "test_example", "test_1")

        assert possible_values == expected

    def test_replace_invalid_char_with_undescore(self):
        username = "test@123"
        email = "test@example.com"

        possible_values = possible_usernames(username, email, n_suffix=2)
        expected = ("test_123", "test", "test_example", "test_123_1")

        assert possible_values == expected

    def test_combine_email_with_domain_name(self):
        username = "test@exampl.com"
        email = "test@example.com"

        possible_values = possible_usernames(username, email, n_suffix=2)
        expected = ("test", "test", "test_example", "test_1")

        assert possible_values == expected

    def test_create_more_possibilities_with_suffixes(self):
        username = "test@exampl.com"
        email = "test@example.com"

        possible_values = possible_usernames(username, email, n_suffix=3)
        expected = ("test", "test", "test_example", "test_1", "test_2")

        assert possible_values == expected


class TestReplaceUsernameWithSuggestions(TestCase):
    def setUp(self):
        self.user_1 = baker.make(User, username="test@", email="test@example.com",)
        self.expected_username_1 = "test"

        self.user_2 = baker.make(User, username="@test@", email="name@example.com")
        #  teste would already exists because of self.username_1
        self.expected_username_2 = "name"

        self.temp_file = NamedTemporaryFile(mode="r")
        self.expected_csv = (
            "old_username,new_username,email\n" "test@,test,test@example.com\n" "@test@,name,name@example.com\n"
        )

    def test_happy_path_wrong_usernames_replacement(self):
        migrate_usernames(filepath=self.temp_file.name)

        self.user_1.refresh_from_db()
        self.user_2.refresh_from_db()
        self.temp_file.seek(0)

        assert self.user_1.username == self.expected_username_1
        assert self.user_2.username == self.expected_username_2
        assert self.temp_file.read() == self.expected_csv

    def test_all_combinations_of_user_1_already_exists(self):
        baker.make(User, username="test")
        baker.make(User, username="test_example")

        migrate_usernames(self.temp_file.name)
        self.expected_username_1 = "test_1"

        self.user_1.refresh_from_db()

        assert self.user_1.username == self.expected_username_1


class TestMigrateDuplicateCaseInsentiveEmails(TestCase):
    """
        Alguns usuários possuem emails duplicados. Algumas das vezes
        variando a duplicação em caixa-baixa e caixa-alta
    """
    def setUp(self):
        self.user_email = "Email@example.com "
        self.user = baker.make(
            User,
            email=self.user_email,
            date_joined=datetime(2020, 1, 1, 0, 0)
        )
        self.same_user = baker.make(
            User,
            email=self.user_email.lower().strip(),
            date_joined=datetime(2020, 1, 2, 0, 0)
        )
        self.regular_user = baker.make(User, email="regular@example.com")

        self.user_token = baker.make(Token, user=self.user)
        self.same_user_token = baker.make(Token, user=self.same_user)

        self.user_state_spreadsheet = baker.make(
            StateSpreadsheet,
            user=self.user
        )
        self.same_user_state_spreadsheet = baker.make(
            StateSpreadsheet,
            user=self.same_user
        )

        self.user_newsletter = baker.make(NewsletterSubscriber, user=self.user)
        self.same_user_newsletter = baker.make(
            NewsletterSubscriber,
            user=self.same_user
        )

    def test_happy_path_migrate_duplicate_emails(self):
        run_migrate_duplicate_emails()

        self.user.refresh_from_db()
        assert self.user.email == self.user_email.lower().strip()

        self.user_token.refresh_from_db()
        self.same_user_token.refresh_from_db()
        assert self.user_token.user == self.user
        assert self.same_user_token.user == self.user

        self.user_state_spreadsheet.refresh_from_db()
        self.same_user_state_spreadsheet.refresh_from_db()
        assert self.user_state_spreadsheet.user == self.user
        assert self.same_user_state_spreadsheet.user == self.user

        self.user_newsletter.refresh_from_db()
        assert self.user_newsletter.user == self.user
        with pytest.raises(NewsletterSubscriber.DoesNotExist):
            self.same_user_newsletter.refresh_from_db()

        with pytest.raises(User.DoesNotExist):
            self.same_user.refresh_from_db()
