from urllib.parse import urljoin

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from core import formatting
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

    def dados_empresas(self):
        fields = [
            {
                "name": "razao_social",
                "title": "Razão Social",
                "type": "text",
                "description": "",
            },
            {
                "name": "qualificacao_responsavel",
                "title": "Qualificação",
                "type": "text",
                "description": "",
            },
            {
                "name": "data_inicio_atividade",
                "title": "Data início",
                "type": "date",
                "description": "",
            },
            {
                "name": "natureza_juridica",
                "title": "Natureza Jurídica",
                "type": "text",
                "description": "",
            },
            {
                "name": "situacao_cadastral",
                "title": "Situação Cadastral",
                "type": "text",
                "description": "",
            },
            {
                "name": "capital_social",
                "title": "Capital Social",
                "type": "text",
                "description": "",
            },
        ]
        empresas = Empresa.objects.filter(person_uuid=self.person_uuid)
        data = {"label": "data", "type": "table", "value": {"fields": fields}}
        rows = []
        for empresa in empresas:
            rows.append(empresa.serialize())

        data["value"]["rows"] = rows
        return data

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


class Empresa(models.Model):
    person_uuid = models.UUIDField(blank=False, null=False, db_index=True)
    cnpj = models.TextField(max_length=14, null=True, blank=True, db_index=True)
    razao_social = models.TextField(max_length=255, null=True, blank=True)
    nome_fantasia = models.TextField(max_length=255, null=True, blank=True)
    cnae = ArrayField(
        models.TextField(
            max_length=7,
            null=True,
            blank=True,
            choices=choices.EMPRESA_CNAE,
        ),
        null=True,
        blank=True,
    )
    data_inicio_atividade = models.DateField(null=True, blank=True)
    data_situacao_cadastral = models.DateField(null=True, blank=True)
    codigo_situacao_cadastral = models.SmallIntegerField(
        null=True, blank=True, choices=choices.EMPRESA_SITUACAO_CADASTRAL
    )
    codigo_motivo_situacao_cadastral = models.SmallIntegerField(
        null=True, blank=True, choices=choices.EMPRESA_MOTIVO_SITUACAO_CADASTRAL
    )
    situacao_especial = models.TextField(max_length=31, null=True, blank=True)
    data_situacao_especial = models.DateField(null=True, blank=True)
    codigo_natureza_juridica = models.SmallIntegerField(
        null=True, blank=True, choices=choices.EMPRESA_NATUREZA_JURIDICA
    )
    codigo_porte = models.SmallIntegerField(null=True, blank=True, choices=choices.EMPRESA_PORTE)
    capital_social = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    opcao_simples = models.BooleanField(null=True, blank=True)
    opcao_mei = models.BooleanField(null=True, blank=True)
    codigo_qualificacao_responsavel = models.SmallIntegerField(
        null=True, blank=True, choices=choices.EMPRESA_QUALIFICACAO_SOCIO
    )

    endereco = models.TextField(max_length=255, null=True, blank=True)
    codigo_municipio = models.SmallIntegerField(null=True, blank=True, choices=choices.MUNICIPIO)
    uf = models.TextField(max_length=2, null=True, blank=True)
    cep = models.TextField(max_length=8, null=True, blank=True)
    cidade_exterior = models.TextField(max_length=255, null=True, blank=True)
    codigo_pais = models.SmallIntegerField(null=True, blank=True, choices=choices.PAIS)

    telefone_1 = models.TextField(max_length=255, null=True, blank=True)
    telefone_2 = models.TextField(max_length=255, null=True, blank=True)
    telefone_fax = models.TextField(max_length=255, null=True, blank=True)
    email = models.TextField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = [models.F("data_situacao_cadastral").desc(nulls_last=True), "cnpj"]
        indexes = [
            models.Index(
                models.F("data_situacao_cadastral").desc(nulls_last=True),
                name="dataset_com_data_sitdesc_idx"
            ),
        ]

    def __str__(self):
        cnpj = formatting.format_cnpj(self.cnpj)
        return f"{cnpj} {self.razao_social}"

    @property
    def f_data_inicio_atividade(self):
        return formatting.format_date(self.data_inicio_atividade)

    @property
    def f_capital_social(self):
        return formatting.format_currency_brl(self.capital_social),

    @property
    def modal_data_type(self):
        return "text"

    @property
    def modal_data_label(self):
        return "Label"

    @property
    def modal_data_value(self):
        return "Value"

    def serialize(self):
        return {
            "id": self.id,
            "razao_social": self.razao_social,
            "qualificacao_responsavel": self.get_codigo_qualificacao_responsavel_display(),
            "data_inicio_atividade": self.f_data_inicio_atividade,
            "natureza_juridica": self.get_codigo_natureza_juridica_display(),
            "situacao_cadastral": self.get_codigo_situacao_cadastral_display(),
            "capital_social": self.f_capital_social,
            "modal_data": {
                "type": self.modal_data_type,
                "label": self.modal_data_label,
                "value": self.modal_data_value,
            },
        }
