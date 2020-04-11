from django.contrib import admin

from covid19.models import StateSpreadsheet
from covid19.forms import state_choices_for_user


class StateFilter(admin.SimpleListFilter):
    title = 'state'
    parameter_name = 'state'

    def lookups(self, request, model_admin):
        return [('', 'Todos')] + state_choices_for_user(request.user)

    def queryset(self, request, queryset):
        state = self.value()
        if state:
            queryset = queryset.from_state(state)
        return queryset


class StateSpreadsheetModelAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'state', 'date', 'status', 'user', 'cancelled']
    list_filter = [StateFilter, 'status', 'cancelled']

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user')
        if not request.user.is_superuser:
            qs = qs.from_user(request.user)
        return qs


admin.site.register(StateSpreadsheet, StateSpreadsheetModelAdmin)
