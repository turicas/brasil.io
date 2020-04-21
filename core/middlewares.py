from django.middleware.cache import FetchFromCacheMiddleware


class NotLoggedUserFetchFromCacheMiddleware(FetchFromCacheMiddleware):

    def process_request(self, request):
        """
        If no auth user, check whether the page is already cached and return
        the cached version if available.
        """
        if not request.user.is_authenticated:
            return super().process_request(request)
