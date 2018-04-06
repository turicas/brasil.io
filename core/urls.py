from django.urls import path

from . import views


app_name = 'core'
urlpatterns = [
    path('', views.index, name='index'),
    path('manifesto', views.manifesto, name='manifesto'),
    path('data/sugira', views.dataset_suggestion, name='dataset-suggestion'),
    path('contato', views.contact, name='contact'),
    path('/api/data', views.dataset_list, name='dataset-list'),
    path('/api/data/<slug>', views.dataset, name='dataset'),
]
