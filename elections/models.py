from urllib.parse import urljoin

from django.db import models
from django.utils import timezone

from elections import choices
from elections.date_utils import get_age


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
    data_nascimento = models.DateField(null=True, blank=True)
    numero_sequencial = models.TextField(max_length=15, null=True, blank=True)
    sigla_partido = models.TextField(max_length=15, null=True, blank=True)
    sigla_unidade_federativa = models.TextField(max_length=2, null=True, blank=True)
    composicao_legenda = models.TextField(null=True, blank=True)
    totalizacao_turno = models.TextField(max_length=16, null=True, blank=True)
    unidade_eleitoral = models.TextField(max_length=32, null=True, blank=True)
    situacao = models.TextField(max_length=15, null=True, blank=True)
    municipio = models.TextField(null=True, blank=True)
    municipio_slug = models.TextField(null=True, blank=True)
    etnia = models.TextField(null=True, blank=True)
    grau_instrucao = models.TextField(null=True, blank=True)
    ocupacao = models.TextField(null=True, blank=True)
    estado_civil = models.TextField(null=True, blank=True)
    numero_urna = models.TextField(null=True, blank=True)

    @classmethod
    def first_year(cls):
        # TODO: cache?
        qs = cls.objects.values("ano").order_by("ano").first()
        return qs["ano"]

    @classmethod
    def get_total(cls):
        return cls.objects.count()

    class Meta:
        ordering = ["-ano"]
        verbose_name = "Candidatura"
        verbose_name_plural = "Candidaturas"
        indexes = [models.Index(fields=["ano"])]

    @property
    def info_list(self):
        default = "Não informado"
        get_field = lambda obj, field: getattr(obj, field, default) or default  # noqa

        def format_nascimento(data_nascimento, default):
            if data_nascimento is None:
                return default

            dtob, age = get_age(data_nascimento)

            return f"{dtob} ({age} anos)"

        def format_coligacao(coligacao, default):
            try:
                partidos = coligacao.split("/")
                if len(partidos) > 1:
                    text = ", ".join(p.strip() for p in partidos[:-1])
                    text += f" e {partidos[-1].strip()}"
                else:
                    return coligacao
            except Exception:
                return default

            return text

        fields = {
            "Coligação": format_coligacao(getattr(self, "composicao_legenda", None), default),
            "Situação candidatura": get_field(self, "situacao"),
            "Nome completo": get_field(self, "nome"),
            "Nome urna": get_field(self, "nome_urna"),
            "Nascimento": format_nascimento(getattr(self, "data_nascimento", None), default),
            "Cor/Raça": get_field(self, "etnia"),
            "Gênero": get_field(self, "genero"),
            "Estado civil": get_field(self, "estado_civil"),
            "Grau de instrução": get_field(self, "grau_instrucao"),
            "Profissão/Ocupação": get_field(self, "ocupacao"),
        }
        type_mapper = {"Situação candidatura": "tag"}
        data = []
        for field, value in fields.items():
            field_type = type_mapper.get(field)
            data.append({"label": field, "value": value})
            if field_type is not None:
                data[-1]["type"] = field_type

        return data

    def social_networks_list(self):
        data = []
        for social_network in self.social_networks.all():
            data.append(
                {
                    "label": social_network.username,
                    "icon": social_network.social_network_metadata.icon,
                    "link": social_network.link
                }
            )

        return data

    def bens_declarados(self):
        data = []
        objs = BemDeclarado.objects.filter(person_uuid=self.person_uuid)
        for obj in objs:
            data.append(
                {
                    "label": obj.get_tipo_display(),
                    "description": obj.descricao,
                    "value": obj.valor,
                }
            )
        total = sum((d["value"] for d in data), 0)
        return data, total

    def __str__(self):
        return f"{self.nome_urna} - {self.cargo} / {self.ano} "


class CandidacyMetadata(models.Model):
    data = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Candidacy Metadata: {self.created_at}"


class SocialNetworkMetadata(models.Model):
    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=255)
    url_prefix = models.URLField(max_length=255)

    class Meta:
        verbose_name = "Social network metadata"
        verbose_name_plural = "Social networks metadata"

    def __str__(self):
        return f"Social Network Metadata: {self.name}"


class CandidacySocialNetwork(models.Model):
    candidacy = models.ForeignKey(
        Candidacy,
        related_name="social_networks",
        on_delete=models.CASCADE
    )
    social_network_metadata = models.ForeignKey(SocialNetworkMetadata, on_delete=models.DO_NOTHING)
    username = models.TextField()
    position = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("position",)
        verbose_name = "Candidacy social network"
        verbose_name_plural = "Candidacy social networks"

    @property
    def link(self):
        return urljoin(self.social_network_metadata.url_prefix, self.username)

    def __str__(self):
        return f"Candidacy Social Network: {self.candidacy} - {self.social_network_metadata}"


class BemDeclarado(models.Model):
    person_uuid = models.UUIDField(blank=False, null=False, db_index=True)
    tipo = models.SmallIntegerField(
        choices=choices.BEM_DECLARADO_TIPO, verbose_name="Tipo", help_text="Tipo do bem declarado"
    )
    valor = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        verbose_name="Valor",
        help_text="Valor do bem, em Reais correntes",
    )
    descricao = models.TextField(
        max_length=512,
        null=True,
        blank=True,
        verbose_name="Descrição",
        help_text="Descrição do bem",
    )

    class Meta:
        ordering = ["-valor"]
        verbose_name = "Bem declarado"
        verbose_name_plural = "Bens declarados"
        indexes = [
            models.Index(fields=["valor"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.valor}"
