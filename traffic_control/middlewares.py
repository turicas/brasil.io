from django.conf import settings
from django.urls import is_valid_path, resolve
from ratelimit import ALL
from ratelimit.core import is_ratelimited
from ratelimit.exceptions import Ratelimited

from traffic_control.constants import RATELIMITED_VIEW_ATTR
from traffic_control.util import ratelimit_key

BLOCKED_REQUEST_ATTR = "_blocked_request"


def block_suspicious_requests(get_response):
    def _raise_exception(request):
        setattr(request, BLOCKED_REQUEST_ATTR, True)
        raise Ratelimited()

    def middleware(request):
        # TODO: DISCLAIMER!!! THIS IS A TEMPORARY HACK TO ESCAPE FROM CURRENT "DDOS ATTACK"
        # WE MUST IMPLEMENT RATE LIMIT CONTROL IN NGINX OR CLOUDFARE SO WE DON'T HAVE TO RELY ON DJANGO TO DO THAT
        agent = request.META.get("HTTP_USER_AGENT", "").lower().strip()
        if not agent or agent in settings.BLOCKED_WEB_AGENTS:
            _raise_exception(request)

        path = request.path
        if settings.APPEND_SLASH and not path.endswith("/"):
            path += "/"

        if is_valid_path(path):
            match = resolve(path)
            if getattr(match.func, RATELIMITED_VIEW_ATTR, None):
                # based in ratelimit decorator
                # https://github.com/jsocol/django-ratelimit/blob/main/ratelimit/decorators.py#L13
                if settings.RATELIMIT_ENABLE and is_ratelimited(
                    request=request,
                    group=None,
                    fn=match.func,
                    key=ratelimit_key,
                    rate=settings.RATELIMIT_RATE,
                    method=ALL,
                    increment=True,
                ):
                    _raise_exception(request)

        return get_response(request)

    return middleware
