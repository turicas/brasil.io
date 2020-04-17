from django.urls import path

from . import views


app_name = "covid19"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("cities/cases", views.cities, name="cities-cases"),
    path("cities/geo", views.cities_geojson, name="cities-geo"),
]
