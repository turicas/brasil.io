from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from traffic_control.models import BlockedRequest


def _max_str(value: str | None, max_size: int) -> str:
    """
    >>> _max_str(None, 10)
    ''
    >>> _max_str('', 10)
    ''
    >>> _max_str('abc', 10)
    'abc'
    >>> _max_str('abcdef', 6)
    'abcdef'
    >>> _max_str('abcdef', 5)
    'ab...'
    """
    value = value or ""
    if len(value) <= max_size:
        return value
    return f"{value[: max_size - 3]}..."


@admin.register(BlockedRequest)
class BlockedRequestAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "status_code",
        "source_ip",
        "user_link",
        "block_reason",
        "path_short",
        "user_agent_short",
    )
    list_filter = ("status_code", "block_reason")
    date_hierarchy = "created_at"
    search_fields = ("source_ip", "path", "user_agent", "user__username", "user__email")
    list_select_related = ("user",)
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "status_code",
        "source_ip",
        "user",
        "block_reason",
        "user_agent",
        "path",
        "headers",
        "query_string",
        "request_data",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Usuário", ordering="user__username")
    def user_link(self, obj):
        if obj.user_id is None:
            return "-"
        if obj.user is None:
            return f"#{obj.user_id} (apagado)"
        url = reverse("admin:auth_user_change", args=[obj.user_id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    @admin.display(description="Path", ordering="path")
    def path_short(self, obj):
        return _max_str(obj.path, 80)

    @admin.display(description="User agent", ordering="user_agent")
    def user_agent_short(self, obj):
        return _max_str(obj.user_agent, 60)
