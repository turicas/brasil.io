from urllib.parse import urlencode

from django.urls import resolve, reverse


class ApiEndpointFromOldVersionException(Exception):
    def __init__(self, request):
        self.request = request

    @property
    def should_redirect_to(self):
        match = resolve(self.request.path)
        url = reverse(f"api-v1:{match.url_name}", args=match.args, kwargs=match.kwargs)

        qs = urlencode(self.request.query_params)
        if qs:
            url += f"?{qs}"

        return url
