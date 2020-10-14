from django.conf import settings
from django.urls.base import set_urlconf


def host_based_url_conf(get_response):
    def middleware(request):
        if request.get_host() == settings.BRASILIO_API_HOST:
            setattr(request, "urlconf", settings.API_ROOT_URLCONF)
        else:
            set_urlconf(None)

        return get_response(request)

    return middleware
