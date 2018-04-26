from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom


class Neo4JNode(GraphObject):

    @property
    def node(self):
        return self.__ogm__.node


class PessoaFisica(Neo4JNode):
    __primarykey__ = "nome"

    nome = Property()
    cpf = Property()

    empresas = RelatedTo("PessoaJuridica", "TEM_SOCIEDADE")


class NomeExterior(Neo4JNode):
    __primarykey__ = "nome"

    nome = Property()
    cpf_cnpj = Property()

    empresas = RelatedTo("PessoaJuridica", "TEM_SOCIEDADE")


class PessoaJuridica(Neo4JNode):
    __primarykey__ = "cnpj"

    nome = Property()
    cnpj = Property()
    uf = Property()

    empresas = RelatedTo("PessoaJuridica", "TEM_SOCIEDADE")
    socios_pj = RelatedFrom("PessoaJuridica", "TEM_SOCIEDADE")
    socios_pf = RelatedFrom("PessoaFisica", "TEM_SOCIEDADE")
    socios_ex = RelatedFrom("NomeExterior", "TEM_SOCIEDADE")
