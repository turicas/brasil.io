from django.urls import path

from . import views


app_name = "covid19"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
