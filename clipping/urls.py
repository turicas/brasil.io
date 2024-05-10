from django.urls import path

from . import views

urlpatterns = [
    path("get/contentype_instances/", views.get_contenttype_instances),
    path("get/selected_instance/", views.get_current_selected_instance),
]
