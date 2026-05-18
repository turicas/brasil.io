from django.contrib import admin

from api.models import Token


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ("key_obfuscated", "user_username", "user_email", "created")
    list_filter = (("created", admin.DateFieldListFilter),)
    list_select_related = ("user",)
    search_fields = ("key", "user__username", "user__email", "user__first_name", "user__last_name")
    autocomplete_fields = ("user",)
    ordering = ("-created",)

    @admin.display(description="Key")
    def key_obfuscated(self, obj):
        return f"{obj.key[:5]}...{obj.key[-5:]}" if obj.key else ""

    @admin.display(description="Login", ordering="user__username")
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description="E-mail", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email

    def get_fields(self, request, obj=None):
        if obj is None:
            return ("user",)
        return ("user", "key_obfuscated", "created")

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return ("user", "key_obfuscated", "created")

    def has_change_permission(self, request, obj=None):
        return False
