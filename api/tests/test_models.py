from django.conf import settings
from django.test import TestCase
from model_bakery import baker

from api.models import Token


class TokenTests(TestCase):
    def test_same_user_can_have_multiple_token(self):
        user = baker.make(settings.AUTH_USER_MODEL)

        token_1, token_2 = baker.make(Token, user=user, _quantity=2)

        assert token_1.key != token_2.key
