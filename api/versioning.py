from decorator import decorator
from django.shortcuts import redirect
from django.urls import resolve, reverse

from api.exceptions import ApiEndpointFromOldVersionException


@decorator
def check_api_version_redirect(func, self, request, *args, **kwargs):
    if request.version == "api-v0":
        raise ApiEndpointFromOldVersionException(request.path)

    return func(self, request, *args, **kwargs)


def redirect_from_older_version(exc):
    if not isinstance(exc, ApiEndpointFromOldVersionException):
        return

    match = resolve(exc.url)
    url = reverse(f"api-v1:{match.url_name}", args=match.args, kwargs=match.kwargs)
    return redirect(url, permanent=True)
