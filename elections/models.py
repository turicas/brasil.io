from django.db import models
from django.utils import timezone


class Candidacy(models.Model):
    id = models.AutoField(primary_key=True)
    person_uuid = models.UUIDField(blank=False, null=False, db_index=True)  # 16 bytes pessoa_uuid

    ano = models.SmallIntegerField(null=True, blank=True)
    cargo = models.TextField(max_length=31, null=True, blank=True)
    cargo_slug = models.SlugField(null=True, blank=True)
    nome = models.TextField(null=True, blank=True)
    nome_urna = models.TextField(max_length=31, null=True, blank=True)
    nome_urna_slug = models.SlugField(null=True, blank=True)
    genero = models.TextField(null=True, blank=True)
    data_nascimento = models.TextField(null=True, blank=True)
    numero_sequencial = models.TextField(max_length=15, null=True, blank=True)
    sigla_partido = models.TextField(max_length=15, null=True, blank=True)
    sigla_unidade_federativa = models.TextField(max_length=2, null=True, blank=True)
    composicao_legenda = models.TextField(null=True, blank=True)
    totalizacao_turno = models.TextField(max_length=16, null=True, blank=True)
    unidade_eleitoral = models.TextField(max_length=32, null=True, blank=True)
    situacao = models.TextField(max_length=15, null=True, blank=True)
    municipio = models.TextField(null=True, blank=True)
    municipio_slug = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-ano"]
        verbose_name = "Candidatura"
        verbose_name_plural = "Candidaturas"
        indexes = [models.Index(fields=["ano"])]

    def __str__(self):
        return f"{self.nome_urna} - {self.cargo} / {self.ano} "


class CandidacyMetadata(models.Model):
    data = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Candidacy Metadata: {self.created_at}"
