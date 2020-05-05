from django.contrib import admin
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


admin.site.register(models.Table, TableAdmin)


class FieldAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("dataset", "version", "table")


admin.site.register(models.Field, FieldAdmin)
