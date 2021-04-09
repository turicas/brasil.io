from django.contrib import admin

from api.models import Token


class TokenAdmin(admin.ModelAdmin):
    list_display = ("key", "user", "created")
    fields = ("user",)
    ordering = ("-created",)
    actions = None  # Actions not compatible with mapped IDs.


admin.site.register(Token, TokenAdmin)
