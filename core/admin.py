from django.contrib import admin, messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import path, reverse
from django.utils.html import format_html
from markdownx.admin import MarkdownxModelAdmin

from core import models


class DatasetAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Dataset, DatasetAdmin)


class LinkAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Link, LinkAdmin)


class VersionAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("dataset")


admin.site.register(models.Version, VersionAdmin)


class TableAdmin(MarkdownxModelAdmin):
    def get_queryset(self, request):
        """
        Return a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = models.Table.with_hidden.all()
        # TODO: this should be handled by some parameter to the ChangeList.
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    list_filter = ["hidden", "dataset__slug", "default"]
    list_display = ["__str__", "enabled_flag"]

    def enabled_flag(self, obj):
        images = {
            True: static("admin/img/icon-yes.svg"),
            False: static("admin/img/icon-no.svg"),
        }
        value = obj.enabled
        title = "Enabled" if value else "Hidden"
        return format_html(f'<img src="{images[value]}" title="{title}" alt="{title}">')

    enabled_flag.short_description = "Enabled"


admin.site.register(models.Table, TableAdmin)


class FieldAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("dataset", "version", "table")


admin.site.register(models.Field, FieldAdmin)


class DataTableAdmin(admin.ModelAdmin):
    ordering = ["-active", "db_table_name"]
    list_display = ["db_table_name", "dataset", "table", "created_at", "active", "manage_activation"]
    list_filter = ["active", "table"]
    readonly_fields = ["db_table_name", "table", "active", "created_at"]
    ACTIVATE_OP, DEACTIVATE_OP = "activate", "deactivate"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("table__dataset")

    def dataset(self, obj):
        return obj.table.dataset.slug

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "manage/<int:data_table_id>/<str:op_type>/",
                self.admin_site.admin_view(self.data_table_management_view),
                name="data_table_management_view",
            ),
        ]
        return custom_urls + urls

    def manage_activation(self, obj):
        if obj.active:
            url = reverse('admin:data_table_management_view', args=[obj.id, self.DEACTIVATE_OP])
            label = "Desativar DataTable"
        else:
            url = reverse('admin:data_table_management_view', args=[obj.id, self.ACTIVATE_OP])
            label = "Ativar DataTable"
        return format_html(f"<a href='{url}'>{label}</a>")
    manage_activation.short_description = "Gerenciar ativação/desativação"

    def data_table_management_view(self, request, data_table_id, op_type):
        if not request.user.is_superuser:
            raise Http404

        data_table = get_object_or_404(models.DataTable, pk=data_table_id)
        context = self.admin_site.each_context(request)
        context["data_table_repr"] = str(data_table)

        if op_type == self.ACTIVATE_OP:
            if data_table.active:
                self.message_user(request, f"{data_table} is already active", messages.WARNING)
                return redirect("admin:core_datatable_changelist")

            current = data_table.table.data_table
            context["action_title"] = "Ativar"
            context[
                "help_text"
            ] = f"Ao desempenhar essa ação, <a href='{current.admin_url}'>{current}</a> será inativado."
            if request.GET.get("confirm", None):
                data_table.activate()
                self.message_user(request, f"{data_table} is now active")
                return redirect(data_table.admin_url)

        elif op_type == self.DEACTIVATE_OP:
            if not data_table.active:
                self.message_user(request, f"{data_table} is already not active", messages.WARNING)
                return redirect("admin:core_datatable_changelist")

            most_recent = data_table.table.data_tables.exclude(id=data_table.id).inactive().most_recent()
            if most_recent:
                context[
                    "help_text"
                ] = f"Ao desempenhar essa ação, <a href='{most_recent.admin_url}'>{most_recent}</a> será ativado."
            else:
                context[
                    "help_text"
                ] = f"<b>CUIDADO!!!</b> A tabela {data_table.table} não possui nenhum outro DataTable associado a ela. Desativar esse DataTable pode gerar efeitos indesejados ao sistema."

            context["action_title"] = "Desativar"
            if request.GET.get("confirm", None):
                data_table.deactivate(activate_most_recent=True)
                self.message_user(request, f"{data_table} is now active")
                return redirect(data_table.admin_url)
        else:
            raise Http404
        return render(request, "admin/data_table_activation_confirm.html", context=context)


admin.site.register(models.DataTable, DataTableAdmin)
