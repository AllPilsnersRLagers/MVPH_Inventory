"""URL configuration for mvph_inventory project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("inventory.urls")),
]
