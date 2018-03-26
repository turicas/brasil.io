from django.contrib import admin

from core import models


class DatasetAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.Dataset, DatasetAdmin)


class LinkAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.Link, LinkAdmin)


class VersionAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('dataset')
admin.site.register(models.Version, VersionAdmin)


class TableAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        return super().get_queryset(request)\
                      .select_related('dataset', 'version')
admin.site.register(models.Table, TableAdmin)


class FieldAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        return super().get_queryset(request)\
                      .select_related('dataset', 'version', 'table')
admin.site.register(models.Field, FieldAdmin)
