from django.contrib import admin

from covid19.models import StateSpreadsheet
from covid19.forms import state_choices_for_user, StateSpreadsheetForm


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
    readonly_fields = ['created_at', 'status', 'cancelled']
    form = StateSpreadsheetForm

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "state":
            kwargs['choices'] = state_choices_for_user(request.user)
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user')
        if not request.user.is_superuser:
            qs = qs.from_user(request.user)
        return qs


admin.site.register(StateSpreadsheet, StateSpreadsheetModelAdmin)
