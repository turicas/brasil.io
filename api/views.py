from collections.abc import Sequence
from functools import lru_cache

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import DatasetDetailSerializer, DatasetSerializer, GenericSerializer
from api.versioning import check_api_version_redirect
from core.filters import parse_querystring
from core.forms import get_table_dynamic_form
from core.models import Dataset, Table
from core.templatetags.utils import obfuscate

from . import paginators


class DatasetViewSet(viewsets.ModelViewSet):
    serializer_class = DatasetSerializer
    queryset = Dataset.objects.api_visible()

    @check_api_version_redirect
    def retrieve(self, request, slug):
        obj = get_object_or_404(self.get_queryset(), slug=slug)
        serializer = DatasetDetailSerializer(
            obj,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @check_api_version_redirect
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)


class InvalidFiltersException(Exception):
    def __init__(self, errors_list):
        self.errors_list = errors_list


class DatasetDataListView(ListAPIView):
    pagination_class = paginators.LargeTablePageNumberPagination

    def get_table(self):
        dataset = get_object_or_404(Dataset.objects.api_visible(), slug=self.kwargs["slug"])
        return get_object_or_404(Table.objects.api_enabled(), dataset=dataset, name=self.kwargs["tablename"])

    def get_model_class(self):
        return self.get_table().get_model()

    def get_queryset(self):
        querystring = self.request.query_params.copy()
        for pagination_key in ("limit", "offset"):
            if pagination_key in querystring:
                del querystring[pagination_key]

        Model = self.get_model_class()
        query, search_query, order_by = parse_querystring(querystring)

        DynamicForm = get_table_dynamic_form(self.get_table())
        filter_form = DynamicForm(data=query)
        if filter_form.is_valid():
            query = {k: v for k, v in filter_form.cleaned_data.items() if v != ""}
        else:
            raise InvalidFiltersException(filter_form.errors)

        return Model.objects.composed_query(query, search_query, order_by)

    def get_serializer_class(self):
        table = self.get_table()
        Model = self.get_model_class()
        fields = sorted([field.name for field in table.fields if field.name != "search_data" and field.show])

        # TODO: move this monkey patch to a metaclass
        GenericSerializer.Meta.model = Model
        GenericSerializer.Meta.fields = fields
        return GenericSerializer

    def get_serializer(self, *args, **kwargs):
        self.get_model_class()  # TODO: avoid to call it twice
        obfuscate_fields = [field.name for field in self.get_table().fields if field.obfuscate and field.show]
        if obfuscate_fields:
            objects = args[0]
            if not isinstance(objects, Sequence):
                objects = [objects]
            for obj in objects:
                for field_name in obfuscate_fields:
                    value = obfuscate(getattr(obj, field_name))
                    setattr(obj, field_name, value)

        return super().get_serializer(*args, **kwargs)

    def handle_exception(self, exc):
        if isinstance(exc, InvalidFiltersException):
            return Response(exc.errors_list, status=400)
        else:
            return super().handle_exception(exc)

    @check_api_version_redirect
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


@lru_cache
def build_api_limits() -> dict:
    return {
        "deep_pagination_records": getattr(settings, "API_MAX_PAGINATION_RECORDS", 0) or None,
        "throttling_rate": getattr(settings, "THROTTLING_RATE", "") or None,
        "max_tokens_per_user": getattr(settings, "MAX_NUM_API_TOKEN_PER_USER", None),
    }


@lru_cache
def build_api_description() -> str:
    parts = [
        "Esta é a API do Brasil.IO. Aqui você poderá acessar os dados disponíveis no",
        "Brasil.IO de maneira automatizada. Porém, a API NÃO é a maneira mais eficiente",
        "de acessar nossos dados! Leia mais em:",
        "https://blog.brasil.io/2020/10/10/como-acessar-os-dados-do-brasil-io/",
        "",
        "IMPORTANTE: a API NÃO foi projetada para você percorrer todas as páginas de um",
        "dataset. Para datasets grandes, baixar o arquivo completo (link na página de",
        "cada dataset em https://brasil.io/datasets/) é dezenas a centenas de vezes",
        "mais rápido que paginar via API, além de não onerar nosso serviço. Os scripts",
        "de coleta são software livre e estão linkados nos metadados de cada dataset.",
    ]

    limits = build_api_limits()
    limit_lines = []
    if limits["deep_pagination_records"]:
        limit_str = f"{limits['deep_pagination_records']:,}".replace(",", ".")
        limit_lines.append(
            f"- Paginação profunda: requisições com (page * page_size) > {limit_str} são rejeitadas com erro 400."
        )
    if limits["throttling_rate"]:
        limit_lines.append(f"- Taxa de requisições por usuário: {limits['throttling_rate']}.")
    if limits["max_tokens_per_user"]:
        limit_lines.append(f"- Máximo de tokens por usuário: {limits['max_tokens_per_user']}.")
    if limit_lines:
        parts.append("")
        parts.append("Limites em vigor:")
        parts.extend(limit_lines)

    parts.extend(
        [
            "",
            "Utilizar a API desnecessariamente e de maneira não otimizada onera muito",
            "nossos servidores e atrapalha a experiência de outros usuários, então",
            "sempre que possível opte por baixar os dados completos.",
            "",
            "O Brasil.IO é um projeto colaborativo, desenvolvido por voluntários e",
            "mantido por financiamento coletivo. Se o projeto é útil para você,",
            "considere fazer uma doação em: https://brasil.io/doe",
        ]
    )
    return "\n".join(parts).strip()


class ApiRootView(APIView):
    @check_api_version_redirect
    def get(self, request):
        data = {
            "title": f"{settings.EMAIL_SUBJECT_PREFIX}Brasil.IO API",
            "version": self.request.version,
            "description": build_api_description(),
            "datasets_url": reverse("v1:dataset-list"),
            "limits": build_api_limits(),
        }
        return Response(data=data)


dataset_list = DatasetViewSet.as_view({"get": "list"})
dataset_detail = DatasetViewSet.as_view({"get": "retrieve"}, lookup_field="slug")
dataset_data = DatasetDataListView.as_view()
api_root = ApiRootView.as_view()
