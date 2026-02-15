"""URL configuration for mvph_inventory project."""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from inventory.views import logout_with_notifications

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", logout_with_notifications, name="logout"),
    path("", include("inventory.urls")),
]
