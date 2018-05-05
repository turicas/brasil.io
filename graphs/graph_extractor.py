import networkx as nx
from graphs.connection import graph_db


def _extract_network(query, path_key='p'):
    graph = nx.DiGraph()
    output = graph_db.run(query)
    while output.forward():
        path = output.current()[path_key]
        nodes = path.nodes()
        rels = path.relationships()

        for node in nodes:
            graph.add_node(
                node.__name__,
                tipo=list(node.labels())[0],
                **node.properties
            )

        for rel in rels:
            graph.add_edge(
                rel.start_node().__name__,
                rel.end_node().__name__,
                tipo_relacao=rel.type(),
                **rel.properties
            )

    return graph


def get_company_network(cnpj, depth=1):
    query = f"""
        MATCH p=((c:PessoaJuridica {{ cnpj: "{cnpj}" }})-[:TEM_SOCIEDADE*{depth}]-(n))
        RETURN p
    """.strip()
    return _extract_network(query)


def get_person_network(name, depth=1):
    name = name.upper()
    query = f"""
        MATCH p=((c:PessoaFisica {{ nome: "{name}" }})-[:TEM_SOCIEDADE*{depth}]-(n))
        RETURN p
    """.strip()
    return _extract_network(query)


def get_foreigner_network(name, depth=1):
    name = name.upper()
    query = f"""
        MATCH p=((c:NomeExterior {{ nome: "{name}" }})-[:TEM_SOCIEDADE*{depth}]-(n))
        RETURN p
    """.strip()
    return _extract_network(query)
