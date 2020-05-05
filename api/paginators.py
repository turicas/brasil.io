from rest_framework import pagination


class LargeTablePageNumberPagination(pagination.PageNumberPagination):

    max_page_size = 10000
    page_size = 1000
    page_size_query_param = "page_size"
