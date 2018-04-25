from py2neo.ogm import GraphObject, Property


class PessoaJuridica(GraphObject):
    __primarykey__ = "cnpj"

    nome = Property()
    cnpj = Property()
    uf = Property()
