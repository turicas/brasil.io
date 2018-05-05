from copy import deepcopy
from rest_framework import serializers

from graphs import graph_extractor


class GraphSerializer(serializers.Serializer):
    nodes = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField()

    def get_nodes(self, network):
        serialized_nodes = []

        for node, data in network.nodes(data=True):
            node_data = deepcopy(data)
            node_data['id'] = str(node)
            serialized_nodes.append(node_data)
        return serialized_nodes

    def get_links(self, network):
        serialized_links = []

        for source, target, data in network.edges(data=True):
            data = deepcopy(data or {})
            link = {'source': str(source), 'target': str(target)}
            link.update(**data)
            serialized_links.append(link)

        return serialized_links


class ResourceNetworkSerializer(serializers.Serializer):
    RESOURCE_TYPES = [
        (1, 'Pessoa Jurídica'),
        (2, 'Pessoa Física'),
        (3, 'Nome Exterior'),
    ]

    tipo = serializers.ChoiceField(choices=RESOURCE_TYPES)
    identificador = serializers.CharField()
    network = serializers.SerializerMethodField()

    def build_graph(self):
        extractors = {
            1: graph_extractor.get_company_network,
            2: graph_extractor.get_person_network,
            3: graph_extractor.get_foreigner_network,
        }
        tipo = self.validated_data['tipo']
        return extractors[tipo](self.validated_data['identificador'])

    def get_network(self, *args, **kwargs):
        network = self.build_graph()
        network_serializer = GraphSerializer(instance=network)
        return network_serializer.data
