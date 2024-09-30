from django.contrib import admin

from elections.models import (
    BemDeclarado,
    Candidacy,
    CandidacyMetadata,
    CandidacySocialNetwork,
    SocialNetworkMetadata,
)


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


class BemDeclaradoAdmin(admin.ModelAdmin):
    pass


class CandidacyMetadataAdmin(admin.ModelAdmin):
    pass


class SocialNetworkMetadataAdmin(admin.ModelAdmin):
    list_display = ("name", "icon")


class CandidacySocialNetworkAdmin(admin.ModelAdmin):
    list_display = ("candidacy", "social_network_metadata", "position", "username", "created_at")
    search_fields = ("username", "social_network_metadata__name")


admin.site.register(BemDeclarado, BemDeclaradoAdmin)
admin.site.register(Candidacy, CandidacyAdmin)
admin.site.register(CandidacyMetadata, CandidacyMetadataAdmin)
admin.site.register(SocialNetworkMetadata, SocialNetworkMetadataAdmin)
admin.site.register(CandidacySocialNetwork, CandidacySocialNetworkAdmin)
