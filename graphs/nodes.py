from py2neo.ogm import GraphObject, Property


class PessoaFisica(GraphObject):
    __primarykey__ = "nome"

    nome = Property()
    cpf = Property()


class PessoaJuridica(GraphObject):
    __primarykey__ = "cnpj"

    nome = Property()
    cnpj = Property()
    uf = Property()


class NomeExterior(GraphObject):
    __primarykey__ = "nome"

    nome = Property()
    cpf_cnpj = Property()
