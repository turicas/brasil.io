from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from api.versioning import check_api_version_redirect
from graphs import serializers
from graphs.exceptions import NodeDoesNotExistException


class GetResourceNetworkView(APIView):
    @check_api_version_redirect
    def get(self, request):
        serializer = serializers.ResourceNetworkSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class GetNodeDataView(APIView):
    @check_api_version_redirect
    def get(self, request):
        serializer = serializers.NodeSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(serializer.data)
        except NodeDoesNotExistException:
            raise Http404


class GetPartnershipPathsView(APIView):
    @check_api_version_redirect
    def get(self, request):
        serializer = serializers.PathSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(serializer.data)
        except NodeDoesNotExistException:
            raise Http404


class GetCompanySubsequentPartnershipsGraphView(APIView):
    @check_api_version_redirect
    def get(self, request):
        serializer = serializers.CompanySubsequentPartnershipsSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(serializer.data)
        except NodeDoesNotExistException:
            raise Http404


class CNPJCompanyGroupsView(APIView):
    @check_api_version_redirect
    def get(self, request):
        serializer = serializers.CNPJCompanyGroupsSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(serializer.data)
        except NodeDoesNotExistException:
            raise Http404
