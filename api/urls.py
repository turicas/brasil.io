from django.urls import path

from graphs import views as graph_views
from traffic_control.decorators import enable_ratelimit

from . import views

app_name = "api-v1"


urlpatterns = [
    # Dataset-related endpoints
    path("", views.api_root, name="api-root"),
    path("datasets/", views.dataset_list, name="dataset-list"),
    path("dataset/<slug>/", views.dataset_detail, name="dataset-detail"),
    path("dataset/<slug>/<tablename>/data/", enable_ratelimit(views.dataset_data), name="dataset-table-data",),
    # Graph-related endpoints
    path("especiais/grafo/sociedades/", graph_views.GetResourceNetworkView.as_view(), name="resource-graph",),
    path(
        "especiais/grafo/sociedades/caminhos/", graph_views.GetPartnershipPathsView.as_view(), name="partnership-paths",
    ),
    path(
        "especiais/grafo/sociedades/subsequentes/",
        graph_views.GetCompanySubsequentPartnershipsGraphView.as_view(),
        name="subsequent-partnerships",
    ),
    path(
        "especiais/grafo/sociedades/empresas-mae/", graph_views.CNPJCompanyGroupsView.as_view(), name="company-groups",
    ),
    path("especiais/grafo/no/", graph_views.GetNodeDataView.as_view(), name="node-data"),
]
