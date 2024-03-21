# Documentação da API

## Coleção de CNPJs e CPFs Brasileiros

**Request:**

`GET`  `/api/dataset/documentos-brasil/documents/data`

**Query String Parameters:**

| Nome          | Tipo          | Descrição                                                    |
| ------------- |:-------------:| ------------------------------------------------------------ |
| document_type | string        | Tipo do documento (CPF ou CNPJ)                              |
| document      | string        | Número do documento                                          |
| name          | string        | Nome de pessoa física ou razão social de pessoa jurídica     |
| sources       | string        | Nome da(s) tabela(s) onde consta o documento.                | 
| docroot       | integer       | Prefixo do Documento. Dígitos iniciais (8) de cada documento, de geração aleatória com propósito de identificação individual e exclusiva |


## Cursos e notas de corte do PROUNI 2018

**Request:**

`GET`  `/api/dataset/cursos-prouni/cursos/data`

**Query String Parameters:**

| Nome                 | Tipo          | Descrição                               |
| ---------------------|:-------------:|---------------------------------------- |
| uf_busca             | string        | UF                                      |
| cidade_busca         | string        | Cidade                                  |
| universidade_nome    | string        | Universidade                            |
| campus_nome          | string        | Nome do Campus                          |
| nome                 | string        | Curso                                   |
| grau                 | string        | Grau                                    |
| turno                | string        | Turno                                   |
| mensalidade          | decimal       | Mensalidade                             |
| bolsa_integral_cotas | integer       | Bolsas Integrais (Cota)                 |
| bolsa_integral_ampla | integer       | Bolsas Integrais (Ampla)                |
| bolsa_parcial_cotas  | integer       | Bolsas Parciais (Cota)                  |
| bolsa_parcial_ampla  | integer       | Bolsas Parciais (Ampla)                 |
| nota_integral_ampla  | decimal       | Nota Integral (Ampla)                   |
| nota_integral_cotas  | decimal       | Nota Integral (Cota)                    |
| nota_parcial_ampla   | decimal       | Nota Parcial (Ampla)                    |
| nota_parcial_cotas   | decimal       | Nota Parcial (Cota)                     |
| curso_busca          | string        | Curso                                   |
| cidade_filtro        | string        | Código da Cidade                        |
| campus_external_id   | integer       | ID do Campus                            |
| curso_id             | string        | ID do Curso                             |


## Eleições Brasil

### Tabela bens_candidatos

**Request:**

`GET`  `/api/dataset/eleicoes-brasil/bens_candidatos/data`

**Query String Parameters:**

| Nome                  | Tipo            | Descrição                                 |
| --------------------- | :-------------: | ----------------------------------------- |
| descricao_eleicao     | string          | Eleição                                   |
| sigla_uf              | string          | UF                                        |
| sq_candidato          | string          | Número Sequencial do Candidato            |
| ds_tipo_bem_candidato | string          | Tipo de Bem                               |
| detalhe_bem           | string          | Detalhe                                   |
| valor_bem             | decimal         | Valor declarado                           |
| ano_eleicao           | integer         | Ano da Eleicão                            |
| cd_tipo_bem_candidato | integer         | Código do Tipo de Bem                     |
