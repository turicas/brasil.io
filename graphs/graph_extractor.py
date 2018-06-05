import networkx as nx
from py2neo.database.selection import NodeSelector

from graphs.connection import get_graph_db_connection


def selector():
    return NodeSelector(get_graph_db_connection())


def _extract_network(query, path_key='p'):
    graph = nx.DiGraph()
    output = get_graph_db_connection().run(query)
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


def get_company_node(cnpj):
    """
    Returns py2neo.types.Node or None
    """
    node = selector().select('PessoaJuridica', cnpj=cnpj).first()
    if not node:
        raise NodeDoesNotExistException()
    return node


def get_person_node(name):
    """
    Returns py2neo.types.Node or None
    """
    node = selector().select('PessoaFisica', nome=name).first()
    if not node:
        raise NodeDoesNotExistException()
    return node


def get_foreigner_node(name):
    """
    Returns py2neo.types.Node or None
    """
    node = selector().select('NomeExterior', nome=name).first()
    if not node:
        raise NodeDoesNotExistException()
    return node


def get_shortest_paths(tipo_1, id_1, tipo_2, id_2, all_shortest_paths=True):
    if tipo_1 == 1:
        source_node_query = f'(s:PessoaJuridica {{ cnpj: "{id_1}" }})'
    elif tipo_1 == 2:
        source_node_query = f'(s:PessoaFisica {{ nome: "{id_1}" }})'
    elif tipo_1 == 3:
        source_node_query = f'(s:NomeExterior {{ nome: "{id_1}" }})'

    if tipo_2 == 1:
        target_node_query = f'(t:PessoaJuridica {{ cnpj: "{id_2}" }})'
    elif tipo_2 == 2:
        target_node_query = f'(t:PessoaFisica {{ nome: "{id_2}" }})'
    elif tipo_2 == 3:
        target_node_query = f'(t:NomeExterior {{ nome: "{id_2}" }})'

    if all_shortest_paths:
        query = f"""
            MATCH {source_node_query},{target_node_query},
            p = allShortestPaths((s)-[:TEM_SOCIEDADE*]-(t))
            return p
        """.strip()
    else:
        query = f"""
            MATCH {source_node_query},{target_node_query},
            p = shortestPath((s)-[:TEM_SOCIEDADE*]-(t))
            return p
        """.strip()

    print(query)
    return _extract_network(query)


def get_company_subsequent_partnerships(cnpj):
    query = f"""
        MATCH (n:PessoaJuridica {{ cnpj: "{cnpj}" }}),
        p=((n)-[:TEM_SOCIEDADE*]->(:PessoaJuridica))
        RETURN p
    """
    return _extract_network(query)


def get_company_groups_cnpj_belongs_to(cnpj):
    query = f"""
        MATCH p=((:EmpresaMae)-[:TEM_SOCIEDADE*]->(:PessoaJuridica {{ cnpj: "{cnpj}" }}))
        RETURN p
    """
    return _extract_network(query)
