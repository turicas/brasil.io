from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls", namespace="api")),
    path("auth/", include("brasilio_auth.urls", namespace="brasilio_auth")),
    path("covid19/", include("covid19.urls", namespace="covid19")),
    path("django-rq/", include("django_rq.urls")),
    path("markdownx/", include("markdownx.urls")),
    path("", include("core.urls", namespace="core")),
]
