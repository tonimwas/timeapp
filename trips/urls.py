from django.urls import path

from . import views

urlpatterns = [
    path("", views.frontend_view, name="frontend"),
    path("api/geo-data/", views.geo_data, name="geo-data"),
    path("api/set-location/", views.set_location, name="set_location"),
]
