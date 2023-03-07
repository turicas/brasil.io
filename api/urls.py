from django.urls import path

from traffic_control.decorators import enable_ratelimit

from . import views

app_name = "v1"


urlpatterns = [
    # Dataset-related endpoints
    path("", views.api_root, name="api-root"),
    path("datasets/", views.dataset_list, name="dataset-list"),
    path("dataset/<slug>/", views.dataset_detail, name="dataset-detail"),
    path("dataset/<slug>/files/", views.dataset_file_list, name="dataset-file-list"),
    path("dataset/<slug>/<tablename>/data/", enable_ratelimit(views.dataset_data), name="dataset-table-data",),
]
