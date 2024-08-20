from django.urls import path

from . import views
from elections.api import CandidacyAPIView

app_name = "election"

urlpatterns = [
    path("api/candidacy/<int:pk>/", CandidacyAPIView.as_view(), name="candidacy_detail"),
    path("index/", views.example, name="example"),
    path("politic/", views.politic, name="politic"),
    path("home/", views.home, name="home"),
]
