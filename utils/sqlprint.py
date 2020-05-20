# Taken from:
# <https://djangosnippets.org/snippets/290/>

import os

from django.conf import settings
from django.db import connection


def terminal_width():
    """Function to compute the terminal width.

    WARNING: This is not my code, but I've been using it forever and I don't
    remember where it came from.
    """

    width = 0
    try:
        import fcntl
        import struct
        import termios

        s = struct.pack("HHHH", 0, 0, 0, 0)
        x = fcntl.ioctl(1, termios.TIOCGWINSZ, s)
        width = struct.unpack("HHHH", x)[1]
    except Exception:
        pass
    if width <= 0:
        try:
            width = int(os.environ["COLUMNS"])
        except Exception:
            pass
    if width <= 0:
        width = 80
    return width


class SqlPrintingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        indentation = 2
        if len(connection.queries) > 0 and settings.DEBUG:
            width = terminal_width()
            total_time = 0.0
            for query in connection.queries:
                nice_sql = query["sql"].replace('"', "").replace(",", ", ")
                sql = "\033[1;31m[{}]\033[0m {}".format(query["time"], nice_sql)
                total_time = total_time + float(query["time"])
                while len(sql) > width - indentation:
                    print("{}{}".format(" " * indentation, sql[: width - indentation]))
                    sql = sql[width - indentation :]  # noqa
                print("{}{}\n".format(" " * indentation, sql))
            replace_tuple = (" " * indentation, str(total_time))
            print("{}\033[1;32m[TOTAL TIME: {} seconds]\033[0m".format(*replace_tuple))

        return response
