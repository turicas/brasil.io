from django.urls import path

from . import views

app_name = "election"
urlpatterns = [
    path("", views.example, name="example"),
    path("politic/", views.politic, name="politic"),
]
