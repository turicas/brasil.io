from django.urls import path

from . import views
from elections.api import CandidacyDetailAPIView, CandidacyListAPIView

app_name = "elections"

urlpatterns = [
    path("api/candidacy/", CandidacyListAPIView.as_view(), name="api_candidacy_list"),
    path("api/candidacy/<int:pk>/", CandidacyDetailAPIView.as_view(), name="api_candidacy_detail"),
    path("index/", views.candidacy_list, name="candidacy_list"),
    path("politic/<int:ano>/<str:uf>/<str:cargo>/<str:nome>/", views.politic, name="candidacy_detail"),
    path("home/", views.home, name="home"),
]
