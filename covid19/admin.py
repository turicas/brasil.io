import csv
import io
from itertools import groupby

from django.conf import settings
from django.contrib import admin, messages
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import path, reverse
from django.utils.html import format_html
from rangefilter.filter import DateRangeFilter

from brazil_data.cities import brazilian_cities_per_state
from brazil_data.states import STATES
from covid19.commands import UpdateStateTotalsCommand
from covid19.forms import StateSpreadsheetForm, state_choices_for_user
from covid19.models import DailyBulletin, StateSpreadsheet
from covid19.permissions import user_has_covid_19_admin_permissions, user_has_state_permission
from covid19.signals import new_spreadsheet_imported_signal
from covid19.spreadsheet_validator import TOTAL_LINE_DISPLAY, UNDEFINED_DISPLAY


def execute_update_state_totals(user):
    stdout = io.StringIO()
    UpdateStateTotalsCommand.execute(user, stdout=stdout)
    stdout.seek(0)
    result, to_order = [], []
    lines = stdout.read().splitlines()
    for line in lines:
        if " - " not in line:  # Not a state status line
            result.append(line)
        else:
            to_order.append(line)
    result.append("")  # Empty line between first messages and state status

    sort_key = lambda line: line.split(" - ")[1]  # noqa
    to_order.sort(key=sort_key)
    for status, group in groupby(to_order, key=sort_key):
        result.append(status)
        result.extend(list(group))
        result.append("")
    return "\n".join(result)


class StateFilter(admin.SimpleListFilter):
    title = "state"
    parameter_name = "state"

    def lookups(self, request, model_admin):
        return [("", "Todos")] + state_choices_for_user(request.user)

    def queryset(self, request, queryset):
        state = self.value()
        if state:
            queryset = queryset.from_state(state)
        return queryset


class ActiveFilter(admin.SimpleListFilter):
    title = "active"
    parameter_name = "active"

    def lookups(self, request, model_admin):
        return [("True", "Ativa"), ("False", "Inativa")]

    def queryset(self, request, queryset):
        active = self.value()
        if active == "True":
            queryset = queryset.filter_active()
        elif active == "False":
            queryset = queryset.filter_inactive()
        return queryset


class StateSpreadsheetModelAdmin(admin.ModelAdmin):
    search_fields = ["user__username", "date"]
    form = StateSpreadsheetForm
    ordering = ["-created_at"]
    add_form_template = "admin/covid19_add_form.html"
    change_list_template = "admin/covid19_list.html"
    actions = ["re_run_import_spreadsheet_action"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "planilha-model/<str:state>/",
                self.admin_site.admin_view(self.sample_spreadsheet_view),
                name="sample_covid_spreadsheet",
            ),
            path("gerenciar", self.admin_site.admin_view(self.covid19_management_view), name="covid19_management",),
        ]
        return custom_urls + urls

    def get_readonly_fields(self, request, obj=None):
        fields = []
        if obj:
            fields.extend(["created_at", "status", "active"])
            fields.extend(StateSpreadsheetForm.Meta.fields + ["peer_link", "warnings_list", "errors_list"])
        return fields

    def get_list_display(self, request):
        list_display = [
            "created_at",
            "state",
            "date",
            "user",
            "status",
            "warnings_list_truncated",
            "peer_link",
            "active",
        ]
        if user_has_covid_19_admin_permissions(request.user):
            list_display.append("automatically_created")
        return list_display

    def get_list_filter(self, request):
        list_filter = [("date", DateRangeFilter), StateFilter, "status", ActiveFilter]
        if user_has_covid_19_admin_permissions(request.user):
            list_filter.append("automatically_created")
        return list_filter

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "state":
            kwargs["choices"] = state_choices_for_user(request.user)
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        is_new = not bool(obj.pk)

        obj.user = request.user
        if is_new:
            self._import_spreadsheet(spreadsheet=obj)
        super().save_model(request, obj, form, change)

    def _import_spreadsheet(self, spreadsheet):
        transaction.on_commit(lambda: new_spreadsheet_imported_signal.send(sender=self, spreadsheet=spreadsheet))

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("user", "peer_review__user")
        if not user_has_covid_19_admin_permissions(request.user):
            qs = qs.from_user(request.user)
        return qs

    def active(self, obj):
        images = {
            True: static("admin/img/icon-yes.svg"),
            False: static("admin/img/icon-no.svg"),
        }
        value = obj.active
        title = "Ativa" if value else "Inativa"
        return format_html(f'<img src="{images[value]}" title="{title}" alt="{title}">')

    def warnings_list(self, obj):
        li_tags = "".join([f"<li>{w}</li>" for w in obj.warnings])
        if not li_tags:
            return "---"
        else:
            return format_html(f"<ul>{li_tags}</ul>")

    warnings_list.short_description = "Warnings"

    def warnings_list_truncated(self, obj):
        max_list = 10
        warnings = obj.warnings[:max_list]
        extra_warnings = len(obj.warnings) - max_list
        if extra_warnings > 0:
            warnings.append(
                f"Existem outros {extra_warnings} warnings. <a href='{obj.admin_url}'>Clique aqui para vê-los</a>"
            )

        li_tags = "".join([f"<li>{w}</li>" for w in warnings])
        if not li_tags:
            return "---"
        else:
            return format_html(f"<ul>{li_tags}</ul>")

    warnings_list_truncated.short_description = "Warnings"

    def peer_link(self, obj):
        if not obj.peer_review:
            return "---"
        else:
            url = reverse("admin:covid19_statespreadsheet_change", args=[obj.peer_review.id])
            return format_html(f'<a href="{url}">{obj.peer_review}</a>')

    peer_link.short_description = "Par de Revisão"

    def errors_list(self, obj):
        li_tags = "".join([f"<li>{w}</li>" for w in obj.errors])
        if not li_tags:
            return "---"
        else:
            return format_html(f"<ul>{li_tags}</ul>")

    errors_list.short_description = "Errors"

    def add_view(self, request, *args, **kwargs):
        extra_context = kwargs.get("extra_context") or {}

        allowed_states = []
        for state in STATES:
            if user_has_state_permission(request.user, state.acronym):
                allowed_states.append(state)

        extra_context["allowed_states"] = allowed_states
        kwargs["extra_context"] = extra_context
        return super().add_view(request, *args, **kwargs)

    def sample_spreadsheet_view(self, request, state):
        try:
            cities = brazilian_cities_per_state()[state]
        except KeyError:
            raise Http404

        if not user_has_state_permission(request.user, state):
            raise Http404

        csv_rows = [
            ("municipio", "confirmados", "mortes"),
            (TOTAL_LINE_DISPLAY, None, None),
            (UNDEFINED_DISPLAY, None, None),
        ] + [(city, None, None) for city in cities]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="modelo-{state}.csv"'

        writer = csv.writer(response)
        writer.writerows(csv_rows)

        return response

    def covid19_management_view(self, request):
        if not user_has_covid_19_admin_permissions(request.user):
            raise Http404
        context = self.admin_site.each_context(request)
        context["state_totals_url"] = settings.COVID_19_STATE_TOTALS_URL.split("export")[0]

        if request.POST.get("action", None) == "update_state_totals":
            context["action_output"] = execute_update_state_totals(request.user)
        return render(request, "admin/covid19_admins_page.html", context=context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["covid19_admin"] = user_has_covid_19_admin_permissions(request.user)
        return super().changelist_view(request, extra_context)

    def re_run_import_spreadsheet_action(self, request, queryset):
        spreadsheets = queryset.order_by("id")
        already_deployed_spreadhseets = [str(s) for s in spreadsheets.deployed()]
        inactive_spreadsheets = [str(s) for s in spreadsheets.filter_inactive()]

        error_msg = ""
        if not user_has_covid_19_admin_permissions(request.user):
            error_msg = "Seu perfil de usuário não tem permissão para executar essa ação."
        elif already_deployed_spreadhseets:
            error_msg = f"Não é possível re-importar planilhas Deployed: {already_deployed_spreadhseets}."
        elif inactive_spreadsheets:
            error_msg = f"Não é possível importar planilhas Inativas: {inactive_spreadsheets}."

        if error_msg:
            self.message_user(request, error_msg, level=messages.ERROR)
            return

        for spreadsheet in spreadsheets:
            self._import_spreadsheet(spreadsheet)

        imported = [str(s) for s in spreadsheets]
        msg = f"O processo para importação de planilhas foi disparado para as seguintes planilhas: {imported}."
        self.message_user(request, msg, level=messages.SUCCESS)

    re_run_import_spreadsheet_action.short_description = "Importar/validar planilhas novamente"


admin.site.register(StateSpreadsheet, StateSpreadsheetModelAdmin)
admin.site.register(DailyBulletin)
