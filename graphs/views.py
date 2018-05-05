from rest_framework.views import APIView
from rest_framework.response import Response

from django.http import Http404

from graphs.exceptions import NodeDoesNotExistException
from graphs.serializers import ResourceNetworkSerializer, NodeSerializer


class GetResourceNetworkView(APIView):

    def get(self, request):
        serializer = ResourceNetworkSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class GetNodeDataView(APIView):

    def get(self, request):
        serializer = NodeSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(serializer.data)
        except NodeDoesNotExistException:
            raise Http404
