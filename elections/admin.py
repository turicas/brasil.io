from django.contrib import admin

from elections.models import Candidacy, CandidacyMetadata


class CandidacyAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "nome_urna",
        "ano",
        "cargo",
        "sigla_partido",
        "sigla_unidade_federativa",
    )
    search_fields = (
        "nome",
        "nome_urna",
        "ano",
        "cargo",
        "sigla_partido",
        "sigla_unidade_federativa",
    )


class CandidacyMetadataAdmin(admin.ModelAdmin):
    pass


admin.site.register(Candidacy, CandidacyAdmin)
admin.site.register(CandidacyMetadata, CandidacyMetadataAdmin)
