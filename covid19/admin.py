from django.contrib import admin
from django.db import transaction
from django.utils.html import format_html

from covid19.forms import state_choices_for_user, StateSpreadsheetForm
from covid19.models import StateSpreadsheet
from covid19.signals import new_spreadsheet_imported_signal


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
    list_display = ['created_at', 'state', 'date', 'user', 'status', 'warnings_list', 'cancelled']
    list_filter = [StateFilter, 'status', 'cancelled']
    form = StateSpreadsheetForm
    ordering = ['-created_at']

    def get_readonly_fields(self, request, obj=None):
        fields = []
        if obj:
            fields.extend(['created_at', 'status', 'cancelled'])
            fields.extend(StateSpreadsheetForm.Meta.fields + ['warnings_list', 'errors_list'])
        return fields

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "state":
            kwargs['choices'] = state_choices_for_user(request.user)
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        is_new = not bool(obj.pk)

        obj.user = request.user
        if is_new:
             transaction.on_commit(
                lambda: new_spreadsheet_imported_signal.send(sender=self, spreadsheet=obj)
            )
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user')
        if not request.user.is_superuser:
            qs = qs.from_user(request.user)
        return qs

    def warnings_list(self, obj):
        li_tags = ''.join([f'<li>{w}</li>' for w in obj.warnings])
        if not li_tags:
            return '---'
        else:
            return format_html(f'<ul>{li_tags}</ul>')
    warnings_list.short_description = "Warnings"

    def errors_list(self, obj):
        li_tags = ''.join([f'<li>{w}</li>' for w in obj.errors])
        if not li_tags:
            return '---'
        else:
            return format_html(f'<ul>{li_tags}</ul>')
    errors_list.short_description = "Errors"


admin.site.register(StateSpreadsheet, StateSpreadsheetModelAdmin)
