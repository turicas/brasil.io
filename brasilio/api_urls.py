from django.urls import include, path

urlpatterns = [
    path("", include("api.urls_v0", namespace="v0")),
    path("v1/", include("api.urls", namespace="v1")),
]

handler403 = "traffic_control.handlers.handler_403"
handler404 = "traffic_control.handlers.handler_404"
handler500 = "traffic_control.handlers.handler_500"
