from django.contrib import admin

from covid19.models import StateSpreadsheet


class StateSpreadsheetModelAdmin(admin.ModelAdmin):
    pass


admin.site.register(StateSpreadsheet, StateSpreadsheetModelAdmin)
