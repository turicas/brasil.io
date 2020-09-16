import functools

from django.conf import settings
from django.middleware.cache import FetchFromCacheMiddleware
from django.middleware.security import SecurityMiddleware
from django.urls import resolve
from ratelimit.exceptions import Ratelimited

DISABLE_CACHE_ATTR = "_disable_non_logged_user_cache"


def disable_non_logged_user_cache(func):

    setattr(func, DISABLE_CACHE_ATTR, True)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


class NotLoggedUserFetchFromCacheMiddleware(FetchFromCacheMiddleware):
    def process_request(self, request):
        """
        If no auth user, check whether the page is already cached and return
        the cached version if available.
        """
        if not request.user.is_authenticated:
            req_info = resolve(request.path)
            if not getattr(req_info.func, DISABLE_CACHE_ATTR, False):
                return super().process_request(request)


class BrasilioSecurityMiddleware(SecurityMiddleware):
    def process_request(self, request):
        # TODO: DISCLAIMER!!! THIS IS A TEMPORARY HACK TO ESCAPE FROM CURRENT "DDOS ATTACK"
        # WE MUST IMPLEMENT RATE LIMIT CONTROL IN NGINX SO WE DON'T HAVE TO RELY ON DJANGO TO DO THAT
        agent = request.META.get("HTTP_USER_AGENT", "").lower().strip()
        if not agent or agent in settings.BLOCKED_WEB_AGENTS:
            import json
            from django_redis import get_redis_connection

            conn = get_redis_connection("default")

            request_data = {
                "query_string": list(request.GET.items()),
                "path": request.path,
                "headers": list(request.headers.items()),
            }
            conn.lpush("blocked", json.dumps(request_data))
            raise Ratelimited()

        return super().process_request(request)
