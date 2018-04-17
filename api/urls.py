from django.urls import path

from . import views


app_name = 'api'
urlpatterns = [
    path('datasets', views.dataset_list, name='dataset-list'),
    path('dataset/<slug>', views.dataset_detail, name='dataset-detail'),
    path('dataset/<slug>/data', views.dataset_data, name='dataset-data'),
]
