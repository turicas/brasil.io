from django.contrib import admin
from django.templatetags.static import static
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
    list_display = ["db_table_name", "dataset", "table", "created_at", "active"]
    list_filter = ["active", "table"]
    readonly_fields = ["db_table_name", "table", "active", "created_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("table__dataset")

    def dataset(self, obj):
        return obj.table.dataset.slug

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


admin.site.register(models.DataTable, DataTableAdmin)
