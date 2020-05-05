import functools

from django.middleware.cache import FetchFromCacheMiddleware
from django.urls import resolve


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
