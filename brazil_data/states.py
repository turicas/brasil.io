from collections import namedtuple


State = namedtuple("State", ["name", "acronym", "ibge_code", "capital_city"])
STATES = [
    State(name="Acre", acronym="AC", ibge_code=12, capital_city="Rio Branco"),
    State(name="Alagoas", acronym="AL", ibge_code=27, capital_city="Maceió"),
    State(name="Amazonas", acronym="AM", ibge_code=13, capital_city="Manaus"),
    State(name="Amapá", acronym="AP", ibge_code=16, capital_city="Macapá"),
    State(name="Bahia", acronym="BA", ibge_code=29, capital_city="Salvador"),
    State(name="Ceará", acronym="CE", ibge_code=23, capital_city="Fortaleza"),
    State(name="Distrito Federal", acronym="DF", ibge_code=53, capital_city="Brasília"),
    State(name="Espírito Santo", acronym="ES", ibge_code=32, capital_city="Vitória"),
    State(name="Goiás", acronym="GO", ibge_code=52, capital_city="Goiânia"),
    State(name="Maranhão", acronym="MA", ibge_code=21, capital_city="São Luís"),
    State(name="Minas Gerais", acronym="MG", ibge_code=31, capital_city="Belo Horizonte"),
    State(name="Mato Grosso do Sul", acronym="MS", ibge_code=50, capital_city="Campo Grande"),
    State(name="Mato Grosso", acronym="MT", ibge_code=51, capital_city="Cuiabá"),
    State(name="Pará", acronym="PA", ibge_code=15, capital_city="Belém"),
    State(name="Paraíba", acronym="PB", ibge_code=25, capital_city="João Pessoa"),
    State(name="Pernambuco", acronym="PE", ibge_code=26, capital_city="Recife"),
    State(name="Piauí", acronym="PI", ibge_code=22, capital_city="Teresina"),
    State(name="Paraná", acronym="PR", ibge_code=41, capital_city="Curitiba"),
    State(name="Rio de Janeiro", acronym="RJ", ibge_code=33, capital_city="Rio de Janeiro"),
    State(name="Rio Grande do Norte", acronym="RN", ibge_code=24, capital_city="Natal"),
    State(name="Rondônia", acronym="RO", ibge_code=11, capital_city="Porto Velho"),
    State(name="Roraima", acronym="RR", ibge_code=14, capital_city="Boa Vista"),
    State(name="Rio Grande do Sul", acronym="RS", ibge_code=43, capital_city="Porto Alegre"),
    State(name="Santa Catarina", acronym="SC", ibge_code=42, capital_city="Florianópolis"),
    State(name="Sergipe", acronym="SE", ibge_code=28, capital_city="Aracaju"),
    State(name="São Paulo", acronym="SP", ibge_code=35, capital_city="São Paulo"),
    State(name="Tocantins", acronym="TO", ibge_code=17, capital_city="Palmas"),
]
STATE_BY_IBGE_CODE = {state.ibge_code: state for state in STATES}
STATE_BY_ACRONYM = {state.acronym: state for state in STATES}
