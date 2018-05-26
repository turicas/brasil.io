from django.urls import path

from . import views
from graphs import views as graph_views


app_name = 'api'
urlpatterns = [
    path('datasets', views.dataset_list, name='dataset-list'),
    path('dataset/<slug>', views.dataset_detail, name='dataset-detail'),
    path('dataset/<slug>/data', views.dataset_data, name='dataset-data'),
    path('especiais/grafo/sociedades', graph_views.GetResourceNetworkView.as_view(), name='resource-graph'),
    path('especiais/grafo/sociedades/caminhos', graph_views.GetPartnershipPathsView.as_view(), name='partnership-paths'),
    path('especiais/grafo/no', graph_views.GetNodeDataView.as_view(), name='node-data'),
]
