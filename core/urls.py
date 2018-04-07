from django.urls import path

from . import api_views, views


app_name = 'core'
urlpatterns = [
    # Institutional pages
    path('', views.index, name='index'),
    path('manifesto', views.manifesto, name='manifesto'),
    path('data/sugira', views.dataset_suggestion, name='dataset-suggestion'),
    path('contato', views.contact, name='contact'),

    # API
    path('api/datasets', api_views.dataset_list, name='dataset-list'),
    path('api/dataset/<slug>', api_views.dataset_detail, name='dataset'),
    path('api/dataset/<slug>/data', api_views.dataset_data, name='dataset-data'),
]
