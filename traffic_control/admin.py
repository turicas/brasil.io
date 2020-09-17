from django.contrib import admin

from traffic_control.models import BlockedRequest


class BlockedRequestAdmin(admin.ModelAdmin):
    readonly_fields = ["request_data", "created_at"]


admin.site.register(BlockedRequest, BlockedRequestAdmin)
