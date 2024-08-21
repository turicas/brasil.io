from django.urls import path

from . import views
from elections.api import CandidacyDetailAPIView, CandidacyListAPIView

app_name = "election"

urlpatterns = [
    path("api/candidacy/", CandidacyListAPIView.as_view(), name="candidacy_list"),
    path("api/candidacy/<int:pk>/", CandidacyDetailAPIView.as_view(), name="candidacy_detail"),
    path("index/", views.example, name="example"),
    path("politic/", views.politic, name="politic"),
    path("home/", views.home, name="home"),
]
