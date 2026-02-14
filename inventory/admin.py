"""Admin configuration for inventory models."""

from __future__ import annotations

from django.contrib import admin

from .models import InventoryItem, Recipe


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin interface for InventoryItem."""

    list_display = [
        "name",
        "category",
        "subcategory",
        "quantity_on_hand",
        "unit_of_measure",
        "earmarked_for",
        "is_low_stock",
    ]
    list_filter = ["category", "subcategory", "earmarked_for"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin interface for Recipe."""

    list_display = ["name", "created_at", "updated_at"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
