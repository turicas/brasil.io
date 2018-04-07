from django.db import connection, models


# TODO: get this data from Dataset model
model_attributes = {
    'socios-brasil': {
        'fields': {
            '__module__': 'core.models',
            'cnpj_empresa': models.CharField(max_length=14),
            'codigo_qualificacao_socio': models.IntegerField(),
            'codigo_tipo_socio': models.IntegerField(),
            'cpf_cnpj_socio': models.CharField(max_length=14),
            'nome_empresa': models.CharField(max_length=255),
            'nome_socio': models.CharField(max_length=255),
            'qualificacao_socio': models.CharField(max_length=127),
            'tipo_socio': models.CharField(max_length=15),
            'unidade_federativa': models.CharField(max_length=2),
        },
        'filtering': ('cnpj_empresa', 'nome_empresa', 'nome_socio'),
        'ordering': ('cnpj_empresa', 'nome_socio'),
    },

    'gastos-diretos': {
        'fields': {
            '__module__': 'core.models',
            'ano': models.IntegerField(),
            'codigo_acao': models.CharField(max_length=4),
            'codigo_elemento_despesa': models.IntegerField(),
            'codigo_favorecido': models.CharField(max_length=112),
            'codigo_funcao': models.IntegerField(),
            'codigo_grupo_despesa': models.IntegerField(),
            'codigo_orgao': models.IntegerField(),
            'codigo_orgao_superior': models.IntegerField(),
            'codigo_programa': models.IntegerField(),
            'codigo_subfuncao': models.IntegerField(),
            'codigo_unidade_gestora': models.IntegerField(),
            'data_pagamento': models.DateField(null=True),
            'data_pagamento_original': models.CharField(max_length=112),
            'gestao_pagamento': models.CharField(max_length=112),
            'linguagem_cidada': models.CharField(max_length=199),
            'mes': models.IntegerField(),
            'nome_acao': models.CharField(max_length=247),
            'nome_elemento_despesa': models.CharField(max_length=113),
            'nome_favorecido': models.CharField(max_length=208),
            'nome_funcao': models.CharField(max_length=21),
            'nome_grupo_despesa': models.CharField(max_length=25),
            'nome_orgao': models.CharField(max_length=45),
            'nome_orgao_superior': models.CharField(max_length=45),
            'nome_programa': models.CharField(max_length=110),
            'nome_subfuncao': models.CharField(max_length=50),
            'nome_unidade_gestora': models.CharField(max_length=45),
            'numero_documento': models.CharField(max_length=112),
            'valor': models.DecimalField(max_digits=12, decimal_places=2),
        },
        'filtering': (
            'nome_orgao_superior', 'nome_unidade_gestora',
            'nome_grupo_despesa', 'nome_elemento_despesa', 'nome_funcao',
            'nome_subfuncao', 'codigo_favorecido', 'nome_favorecido',
        ),
        'ordering': ('-data_pagamento', 'nome_favorecido'),
    },
}


def get_model(slug):
    model_name = ''.join([word.capitalize() for word in slug.split('-')])
    if slug not in registry:
        attrs = model_attributes[slug]
        registry[slug] = type(
            model_name,
            (models.Model,),
            attrs['fields'],
        )
        # TODO: add Meta.ordering

    return registry[slug]


def create_tables():
    from textwrap import dedent
    # TODO: must get all tables from database
    # TODO: check if table/index already created before trying to create it
    # TODO: indices must be expressed as meta-data and automatically
    # created
    SociosBrasil = get_model('socios-brasil')
    fields = [(f.name, f) for f in SociosBrasil._meta.local_fields]
    table_name = SociosBrasil._meta.db_table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(SociosBrasil)
    with connection.cursor() as cursor:
        # TODO: get index info from ordering
        cursor.execute(dedent('''
            CREATE INDEX idx_core_sociosbrasil
            ON core_sociosbrasil
            (cnpj_empresa ASC, nome_socio ASC);
        '''))
        # TODO: get fts fields info from filtering
        cursor.execute(dedent('''
            CREATE INDEX idx_core_sociosbrasil_text
            ON core_sociosbrasil
            USING GIN (to_tsvector('portuguese', cnpj_empresa || ' ' || nome_empresa || ' ' || nome_socio));
        '''))

    GastosDiretos = get_model('gastos-diretos')
    fields = [(f.name, f) for f in GastosDiretos._meta.local_fields]
    table_name = GastosDiretos._meta.db_table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(GastosDiretos)
    with connection.cursor() as cursor:
        cursor.execute(dedent('''
            CREATE INDEX idx_core_gastosdiretos
            ON core_gastosdiretos
            (data_pagamento DESC, nome_favorecido ASC);
        '''))
        cursor.execute(dedent('''
            CREATE INDEX idx_core_gastosdiretos_text
            ON core_gastosdiretos
            USING GIN (to_tsvector('portuguese', nome_orgao_superior || ' ' || nome_unidade_gestora || ' ' || nome_grupo_despesa || ' ' || nome_elemento_despesa || ' ' || nome_funcao || ' ' || nome_subfuncao || ' ' || codigo_favorecido || ' ' || nome_favorecido));
        '''))


registry = {}
