from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("brasilio.api_urls")),
    path("auth/", include("brasilio_auth.urls", namespace="brasilio_auth")),
    path("covid19/", include("covid19.urls", namespace="covid19")),
    path("clipping/", include("clipping.urls")),
    path("django-rq/", include("django_rq.urls")),
    path("markdownx/", include("markdownx.urls")),
    path("", include("core.urls", namespace="core")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "traffic_control.handlers.handler_403"
handler404 = "traffic_control.handlers.handler_404"
handler500 = "traffic_control.handlers.handler_500"
