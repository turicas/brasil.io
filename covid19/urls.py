from django.urls import path

from . import views

app_name = "covid19"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("status/", views.status, name="status"),
    path("status/<str:state>/", views.state_status, name="state_status"),
    path("boletins/", views.list_bulletins, name="bulletins"),
    path("voluntarios/", views.volunteers, name="volunteers"),
    path("cities/cases/", views.cities, name="cities-cases"),
    path("historical/daily/", views.historical_daily, name="historical-daily"),
    path("historical/weekly/", views.historical_weekly, name="historical-weekly"),
    path("cities/geo/", views.cities_geojson, name="cities-geo"),
    path("states/geo/", views.states_geojson, name="states-geo"),
    path("import-data/<str:state>/", views.import_spreadsheet_proxy, name="spreadsheet_proxy"),
    path("<str:state>/", views.dashboard, name="dashboard"),
]
