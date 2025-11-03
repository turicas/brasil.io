import csv

from django.http import HttpResponse
from django.utils.translation import gettext as _


def get_field_value(obj, field, has_choices):
    if has_choices:
        return getattr(obj, f"get_{field}_display")()
    else:
        return getattr(obj, field)


class ExportCsvMixin:
    # Adapted from
    # <https://books.agiliq.com/projects/django-admin-cookbook/en/latest/export.html>
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename={}.csv".format(meta)
        fields_has_choices = {field.name: field.choices is not None for field in meta.fields}
        field_names = list(fields_has_choices.keys())
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([get_field_value(obj, field, fields_has_choices[field]) for field in field_names])
        return response

    export_as_csv.short_description = _("Export as CSV")
