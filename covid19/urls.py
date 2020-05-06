from django.urls import include, path, register_converter
from datetime import datetime

from . import views


# From: https://stackoverflow.com/questions/41212865/django-url-that-captures-yyyy-mm-dd-date
class DateConverter:
    regex = '\d{4}-\d{2}-\d{2}'

    def to_python(self, value):
        return datetime.strptime(value, '%Y-%m-%d')

    def to_url(self, value):
        return value


register_converter(DateConverter, 'ymd')

app_name = 'covid19'

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("status/", views.status, name="status"),
    path("voluntarios/", views.volunteers, name="volunteers"),
    path("cities/cases/", views.cities, name="cities-cases"),
    path("cities/geo/", views.cities_geojson, name="cities-geo"),
    path("states/geo/", views.states_geojson, name="states-geo"),
    path("import-data/<str:state>/", views.import_spreadsheet_proxy, name="spreadsheet_proxy"),
    path('api/import-data/<str:state>/<ymd:date>/', views.StateSpreadsheetViewList.as_view(), name='statespreadsheet-list'),
    path('api/import-data/<str:state>/<ymd:date>/<int:pk>/', views.StateSpreadsheetViewDetail.as_view(), name='statespreadsheet-detail'),
    path("<str:state>/", views.dashboard, name="dashboard"),
]
