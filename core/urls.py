from django.urls import path

from . import views


app_name = 'core'
urlpatterns = [
    path('', views.index, name='index'),
    path('contato', views.contact, name='contact'),
    path('datasets', views.dataset_list, name='dataset-list'),
    path('dataset/<slug>', views.dataset_detail, name='dataset-detail'),
    path('datasets/sugira', views.dataset_suggestion, name='dataset-suggestion'),
    path('manifesto', views.manifesto, name='manifesto'),
]
