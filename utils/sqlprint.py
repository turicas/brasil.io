# Taken from:
# <https://djangosnippets.org/snippets/290/>

import os

from django.conf import settings
from django.db import connection


class SqlPrintingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if settings.DEBUG and len(connection.queries) > 0:
            total_time = 0.0
            for query in connection.queries:
                sql = query["sql"]
                query_time = float(query["time"])
                total_time += query_time
                colored_query = "\033[1;31m[{}]\033[0m {}".format(query_time, sql)
                print(colored_query)
            print("\033[1;32m[TOTAL QUERY TIME: {} seconds]\033[0m".format(total_time))

        return response
