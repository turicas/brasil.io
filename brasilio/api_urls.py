from django.urls import include, path

urlpatterns = [
    path("", include("api.urls_v0", namespace="api-v0")),
    path("v1/", include("api.urls", namespace="api-v1")),
]

handler403 = "traffic_control.handlers.handler_403"
