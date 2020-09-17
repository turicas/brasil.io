from django.conf import settings
from django.urls import path
from ratelimit.decorators import ratelimit

from graphs import views as graph_views
from traffic_control.util import ratelimit_key

from . import views

app_name = "api"


def limited_dataset_data(request, slug, tablename):
    # cannot use @decorator syntax because reading from settings during import time
    # prevents django.test.override_settings from working as expected.
    # that's why I'm manually decorating the view in this custom view
    return ratelimit(key=ratelimit_key, rate=settings.RATELIMIT_RATE, block=settings.RATELIMIT_ENABLE)(
        views.dataset_data
    )(request, slug=slug, tablename=tablename)


urlpatterns = [
    # Dataset-related endpoints
    path("datasets/", views.dataset_list, name="dataset-list"),
    path("dataset/<slug>/", views.dataset_detail, name="dataset-detail"),
    path("dataset/<slug>/<tablename>/data/", limited_dataset_data, name="dataset-table-data",),
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
