"""Admin configuration for inventory models."""

from __future__ import annotations

from django.contrib import admin

from .models import InventoryItem, Recipe, RecipeIngredient


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin interface for InventoryItem."""

    list_display = [
        "name",
        "manufacturer",
        "category",
        "subcategory",
        "quantity_on_hand",
        "unit_of_measure",
        "earmarked_recipes",
        "is_low_stock",
    ]
    list_filter = ["category", "subcategory", "manufacturer"]
    search_fields = ["name", "manufacturer", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    filter_horizontal = ["earmarked_for"]

    @admin.display(description="Earmarked For")
    def earmarked_recipes(self, obj: InventoryItem) -> str:
        """Display earmarked recipes as comma-separated list."""
        recipes = obj.earmarked_for.all()
        if recipes:
            return ", ".join(r.name for r in recipes)
        return "—"


class RecipeIngredientInline(admin.TabularInline):  # type: ignore[type-arg]
    """Inline admin for recipe ingredients."""

    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin interface for Recipe."""

    list_display = ["name", "abv", "ibu", "ingredient_count", "created_at"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [RecipeIngredientInline]

    @admin.display(description="Ingredients")
    def ingredient_count(self, obj: Recipe) -> int:
        """Display count of ingredients in the recipe."""
        return obj.ingredients.count()
