from django.contrib import admin

from covid19.models import StateSpreadsheet


class StateSpreadsheetModelAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'state', 'date', 'status', 'user', 'cancelled']

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user')
        if not request.user.is_superuser:
            qs = qs.from_user(request.user)
        return qs


admin.site.register(StateSpreadsheet, StateSpreadsheetModelAdmin)
