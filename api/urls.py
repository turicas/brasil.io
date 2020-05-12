from django.urls import path

from graphs import views as graph_views

from . import views

app_name = "api"
urlpatterns = [
    # Dataset-related endpoints
    path("datasets/", views.dataset_list, name="dataset-list"),
    path("dataset/<slug>/", views.dataset_detail, name="dataset-detail"),
    path("dataset/<slug>/<tablename>/data/", views.dataset_data, name="dataset-table-data",),
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
