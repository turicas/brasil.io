import binascii
import os

from django.conf import settings
from django.db import models


class Token(models.Model):
    """
    Same as DRF Token model, but allowing more than one token per user
    """

    key = models.CharField("Key", max_length=40, primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="auth_tokens", on_delete=models.CASCADE, verbose_name="User"
    )
    created = models.DateTimeField("Created", auto_now_add=True)

    class Meta:
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    @classmethod
    def generate_key(cls):
        return binascii.hexlify(os.urandom(20)).decode()

    @classmethod
    def num_of_available_tokens(cls, user):
        return settings.MAX_NUM_API_TOKEN_PER_USER - user.auth_tokens.count()

    def __str__(self):
        return self.key
