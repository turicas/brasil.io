from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views, views_special


app_name = 'core'
urlpatterns = [
    # Institutional pages
    path('', views.index, name='index'),
    path('contato', views.contact, name='contact'),
    path('datasets', views.dataset_list, name='dataset-list'),
    path('home', views.home, name='home'),
    path('dataset/<slug>', views.dataset_detail, name='dataset-detail'),
    path('dataset/<slug>/<tablename>', views.dataset_detail, name='dataset-table-detail'),
    path('datasets/sugira', views.dataset_suggestion, name='dataset-suggestion'),
    path('manifesto', views.manifesto, name='manifesto'),

    # Dataset-specific pages (specials)
    path('especiais', login_required(views_special.index), name='specials'),
    path('especiais/documento/<document>', login_required(views_special.document_detail), name='special-document-detail'),
    path('especiais/caminho', login_required(views_special.trace_path), name='special-trace-path'),
]
