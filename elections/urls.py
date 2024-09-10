from django.urls import path

from . import views

app_name = "elections"

urlpatterns = [
    path("", views.candidacy_redirect_2024, name="redirect_2024"),
    path("2024/", views.candidacy_list, name="candidacy_list"),
    path(
        "2024/<int:ano>/<str:uf>/<str:cargo>/<str:nome>/",
        views.politic,
        name="candidacy_detail"
    ),
    path("home/", views.home, name="home"),
]
