from django.contrib import admin
from django.contrib.auth import get_user_model

from api.models import Token

User = get_user_model()


class TokenAdmin(admin.ModelAdmin):
    list_display = ("key", "user", "created")
    fields = ("user",)
    ordering = ("-created",)
    actions = None  # Actions not compatible with mapped IDs.


admin.site.register(Token, TokenAdmin)
