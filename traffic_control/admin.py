from django.contrib import admin

from traffic_control.models import BlockedRequest


class BlockedRequestAdmin(admin.ModelAdmin):
    readonly_fields = ["request_data", "created_at"]
    list_display = ["source_ip", "status_code", "path", "user_agent", "created_at"]


admin.site.register(BlockedRequest, BlockedRequestAdmin)
