from rest_framework.views import APIView
from rest_framework.response import Response

from graphs.serializers import ResourceNetworkSerializer


class GetResourceNetworkView(APIView):

    def get(self, request):
        serializer = ResourceNetworkSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
