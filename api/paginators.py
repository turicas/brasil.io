from functools import lru_cache

from django.conf import settings
from rest_framework import pagination

from api.exceptions import DeepPaginationNotAllowed

API_MAX_PAGINATION_RECORDS = getattr(settings, "API_MAX_PAGINATION_RECORDS", 0) or 0


@lru_cache
def _dataset_code_url(slug: str) -> str | None:
    from core.models import Dataset

    return Dataset.objects.filter(slug=slug).values_list("code_url", flat=True).first()


class LargeTablePageNumberPagination(pagination.PageNumberPagination):
    max_page_size = 10000
    page_size = 1000
    page_size_query_param = "page_size"

    def paginate_queryset(self, queryset, request, view=None):
        self._enforce_deep_pagination_limit(request, view)
        return super().paginate_queryset(queryset, request, view=view)

    def _enforce_deep_pagination_limit(self, request, view):
        if API_MAX_PAGINATION_RECORDS <= 0:
            return

        page_size = self.get_page_size(request)
        if not page_size:
            return

        try:
            page = int(request.query_params.get(self.page_query_param, 1))
        except (TypeError, ValueError):
            return

        if page <= 0:
            return

        if page * page_size > API_MAX_PAGINATION_RECORDS:
            slug = getattr(view, "kwargs", {}).get("slug") if view else None
            raise DeepPaginationNotAllowed(
                page=page,
                page_size=page_size,
                limit=API_MAX_PAGINATION_RECORDS,
                dataset_slug=slug,
                code_url=_dataset_code_url(slug) if slug else None,
            )
