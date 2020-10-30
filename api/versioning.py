from decorator import decorator
from django.shortcuts import redirect

from api.exceptions import ApiEndpointFromOldVersionException


@decorator
def check_api_version_redirect(func, self, request, *args, **kwargs):
    if request.version == "api-v0":
        raise ApiEndpointFromOldVersionException(request)

    return func(self, request, *args, **kwargs)


def redirect_from_older_version(exc):
    if not isinstance(exc, ApiEndpointFromOldVersionException):
        return

    return redirect(exc.should_redirect_to, permanent=True)
