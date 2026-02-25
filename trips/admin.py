from django.contrib import admin

from .models import Neighbourhood, Place


@admin.register(Neighbourhood)
class NeighbourhoodAdmin(admin.ModelAdmin):
    list_display = ("name", "lat", "lng")
    search_fields = ("name",)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "category", "neighbourhood", "price_tier")
    list_filter = ("category", "price_tier", "neighbourhood")
    search_fields = ("slug", "name")
