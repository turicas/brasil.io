from urllib.parse import urlencode

from django.urls import resolve, reverse
from rest_framework.exceptions import APIException


class ApiEndpointFromOldVersionException(Exception):
    def __init__(self, request):
        self.request = request

    @property
    def should_redirect_to(self):
        match = resolve(self.request.path)
        url = reverse(f"v1:{match.url_name}", args=match.args, kwargs=match.kwargs)
        qs = urlencode(self.request.query_params)
        if qs:
            url += f"?{qs}"
        return url


class DeepPaginationNotAllowed(APIException):
    status_code = 400
    default_code = "deep_pagination_not_allowed"

    def __init__(
        self,
        page: int,
        page_size: int,
        limit: int,
        dataset_slug: str | None = None,
        code_url: str | None = None,
    ):
        self.page = page
        self.page_size = page_size
        self.limit = limit
        self.dataset_slug = dataset_slug
        self.code_url = code_url
        super().__init__(detail=self._build_message(), code=self.default_code)

    def _build_message(self) -> str:
        if self.dataset_slug:
            dataset_link = (
                f"Baixe o dataset completo em https://brasil.io/dataset/{self.dataset_slug}/ "
                "(o link para o arquivo completo está nessa página). "
            )
        else:
            dataset_link = (
                "Encontre o link para o arquivo completo na página do dataset em https://brasil.io/datasets/. "
            )
        if self.code_url:
            code_link = (
                f"O código de coleta deste dataset (software livre) está em {self.code_url} "
                "- baixar e rodar localmente costuma ser dezenas de vezes mais rápido "
                "que paginar via API."
            )
        else:
            code_link = "Os scripts de coleta são software livre e estão linkados nos metadados do dataset."
        limite = f"{self.limit:,}".replace(",", ".")
        requested = f"{self.page * self.page_size:,}".replace(",", ".")
        return (
            f"Você ultrapassou o limite de paginação da API ({limite} registros). "
            f"A requisição atual atingiria {requested} registros "
            f"(page={self.page}, page_size={self.page_size}).\n"
            "Percorrer todas as páginas de um dataset via API é a forma mais lenta "
            "de obtê-lo e sobrecarrega o serviço, prejudicando outros usuários. "
            f"{dataset_link}{code_link}\n"
            "Lembre-se de que o Brasil.IO é um projeto mantido voluntariamente - colabore doando https://brasil.io/doe/"
        )
