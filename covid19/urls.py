from django.urls import path

from . import views


app_name = "covid19"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("voluntarios", views.volunteers, name="volunteers"),
    path("cities/cases", views.cities, name="cities-cases"),
    path("cities/geo", views.cities_geojson, name="cities-geo"),
    path("import-data/<str:state>/", views.import_spreadsheet_proxy, name="spreadsheet_proxy"),
]
