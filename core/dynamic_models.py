from django.db import models


attrs_sociosbrasil = {
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
}
SociosBrasil = type('SociosBrasil', (models.Model,), attrs_sociosbrasil)


attrs_gastosdiretos = {
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
    'data_pagamento': models.DateField(),
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
    'valor': models.DecimalField(),
}
GastosDiretos = type('GastosDiretos', (models.Model,), attrs_gastosdiretos)


register = {
    'socios-brasil': SociosBrasil,
    'gastos-diretos': GastosDiretos,
}
options = {
    'socios-brasil': {'ordering': ('nome_empresa', 'nome_socio')},
    'gastos-diretos': {'ordering': ('-data_pagamento', 'nome_favorecido')},
}
