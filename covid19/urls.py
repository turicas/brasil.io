from django.urls import include, path, register_converter
from datetime import datetime

from . import views

app_name = 'covid19'

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("status/", views.status, name="status"),
    path("voluntarios/", views.volunteers, name="volunteers"),
    path("cities/cases/", views.cities, name="cities-cases"),
    path("cities/geo/", views.cities_geojson, name="cities-geo"),
    path("states/geo/", views.states_geojson, name="states-geo"),
    path("import-data/<str:state>/", views.import_spreadsheet_proxy, name="spreadsheet_proxy"),
    path('api/import-data/<str:state>/', views.StateSpreadsheetViewList.as_view(), name='statespreadsheet-list'),
    path("<str:state>/", views.dashboard, name="dashboard"),
]
