# Based on: <https://djangosnippets.org/snippets/290/>
import sqlparse
from django.conf import settings
from django.db import connection


class SqlPrintingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if settings.DEBUG and len(connection.queries) > 0:
            total_time = 0.0
            for counter, query in enumerate(connection.queries, start=1):
                sql = sqlparse.format(query["sql"], reindent=True, keyword_case="upper").strip()
                query_time = float(query["time"])
                total_time += query_time
                colored_query = "\033[1;31mQUERY {} ({:.5f}s):\033[0m\n{}".format(counter, query_time, sql)
                print(colored_query)
            print("\033[1;32mTOTAL QUERY TIME: {:.5f}s\033[0m".format(total_time))

        return response
