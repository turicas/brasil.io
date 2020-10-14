import functools

import rest_framework
from django.middleware.cache import FetchFromCacheMiddleware
from django.urls import resolve
from django.urls.base import get_urlconf

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

        if not self.should_skip_cache(request):
            return super().process_request(request)

    def should_skip_cache(self, request):
        req_info = resolve(request.path, urlconf=get_urlconf())

        disable = getattr(req_info.func, DISABLE_CACHE_ATTR, False)
        if disable:
            return True

        if request.user.is_authenticated:
            return True

        # Django Rest Framework authentication happens at view-level, not middleware
        # So, any specific authentication, such as TokenAuthentication will run after that
        # This cache ignores API views.
        view_class = getattr(req_info.func, "cls", None)
        drf_views = (rest_framework.views.APIView, rest_framework.viewsets.ViewSet)
        if view_class and issubclass(view_class, drf_views):
            return True

        return False
