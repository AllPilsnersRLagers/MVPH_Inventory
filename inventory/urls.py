"""URL routes for inventory app."""

from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.item_list, name="item_list"),
    path("items/create/", views.item_create, name="item_create"),
    path("items/<uuid:pk>/", views.item_detail, name="item_detail"),
    path("items/<uuid:pk>/edit/", views.item_update, name="item_update"),
    path("items/<uuid:pk>/delete/", views.item_delete, name="item_delete"),
    path(
        "items/<uuid:pk>/adjust-stock/",
        views.adjust_stock,
        name="adjust_stock",
    ),
    path(
        "items/subcategory-options/",
        views.subcategory_options,
        name="subcategory_options",
    ),
    # Recipe management
    path("recipes/", views.recipe_list, name="recipe_list"),
    path("recipes/create/", views.recipe_create, name="recipe_create"),
    path("recipes/<uuid:pk>/edit/", views.recipe_update, name="recipe_update"),
    path("recipes/<uuid:pk>/delete/", views.recipe_delete, name="recipe_delete"),
    path("recipes/quick-add/", views.recipe_quick_add, name="recipe_quick_add"),
]
