from django.contrib import admin

from .models import Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "category", "neighbourhood", "price_tier")
    list_filter = ("category", "price_tier", "neighbourhood")
    search_fields = ("slug", "name")
