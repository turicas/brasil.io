from django.urls import path

from . import views

app_name = "elections"

urlpatterns = [
    path("index/", views.candidacy_list, name="candidacy_list"),
    path("politic/<int:ano>/<str:uf>/<str:cargo>/<str:nome>/", views.politic, name="candidacy_detail"),
    path("home/", views.home, name="home"),
]
