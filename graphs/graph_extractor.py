import networkx as nx
from graphs.connection import graph_db


def get_company_network(cnpj, depth):
    query = f"""
        MATCH p=((c:PessoaJuridica {{ cnpj: "{cnpj}" }})-[:TEM_SOCIEDADE*{depth}]-(n))
        RETURN p
    """.strip()

    graph = nx.DiGraph()
    output = graph_db.run(query)
    while output.forward():
        path = output.current()['p']
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
