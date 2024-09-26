from django.urls import path

from . import views

app_name = "elections"

urlpatterns = [
    path("", views.home, name="home"),
    path("2024/", views.candidacy_list, name="candidacy_list"),
    path(
        "<int:ano>/<str:uf>/<str:municipio>/<str:cargo>/<str:nome>/",
        views.politic,
        name="candidacy_detail"
    ),
    path("sobre/", views.about, name="about"),
    path("politica-de-privacidade/", views.privacy_policy, name="privacy_policy"),
]
