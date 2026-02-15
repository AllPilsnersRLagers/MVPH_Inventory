"""Inventory models for brewery inventory management."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class Category(models.TextChoices):
    """Top-level item categories."""

    INGREDIENT = "ingredient", "Ingredient"
    CHEMICAL = "chemical", "Chemical"
    FINISHED_GOOD = "finished_good", "Finished Good"


class Subcategory(models.TextChoices):
    """Item subcategories, dependent on parent category."""

    # Ingredients
    MALT = "malt", "Malt"
    HOPS = "hops", "Hops"
    YEAST = "yeast", "Yeast"
    ADJUNCT = "adjunct", "Adjunct"
    FRUIT_FLAVOR = "fruit_flavor", "Fruit/Flavor"
    # Chemicals
    CLEANER = "cleaner", "Cleaner"
    SANITIZER = "sanitizer", "Sanitizer"
    WATER_TREATMENT = "water_treatment", "Water Treatment"
    # Finished Goods
    KEG = "keg", "Keg"
    CAN = "can", "Can"
    BOTTLE = "bottle", "Bottle"
    CASE = "case", "Case"


SUBCATEGORY_MAP: dict[str, list[tuple[str, str]]] = {
    Category.INGREDIENT: [
        (Subcategory.MALT, Subcategory.MALT.label),
        (Subcategory.HOPS, Subcategory.HOPS.label),
        (Subcategory.YEAST, Subcategory.YEAST.label),
        (Subcategory.ADJUNCT, Subcategory.ADJUNCT.label),
        (Subcategory.FRUIT_FLAVOR, Subcategory.FRUIT_FLAVOR.label),
    ],
    Category.CHEMICAL: [
        (Subcategory.CLEANER, Subcategory.CLEANER.label),
        (Subcategory.SANITIZER, Subcategory.SANITIZER.label),
        (Subcategory.WATER_TREATMENT, Subcategory.WATER_TREATMENT.label),
    ],
    Category.FINISHED_GOOD: [
        (Subcategory.KEG, Subcategory.KEG.label),
        (Subcategory.CAN, Subcategory.CAN.label),
        (Subcategory.BOTTLE, Subcategory.BOTTLE.label),
        (Subcategory.CASE, Subcategory.CASE.label),
    ],
}


class UnitOfMeasure(models.TextChoices):
    """Units of measure for inventory items."""

    LB = "lb", "lb"
    OZ = "oz", "oz"
    G = "g", "g"
    KG = "kg", "kg"
    GAL = "gal", "gal"
    L = "L", "L"
    ML = "mL", "mL"
    EACH = "each", "each"
    PACK = "pack", "pack"


class Recipe(models.Model):
    """A recipe that ingredients can be earmarked for."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    abv = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="ABV %",
        help_text="Alcohol by volume percentage",
    )
    ibu = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="IBU",
        help_text="International Bitterness Units",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recipes_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recipes_updated",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class InventoryItem(models.Model):
    """A single inventory item tracked by the brewery."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=Category.choices)
    subcategory = models.CharField(max_length=20, choices=Subcategory.choices)
    description = models.TextField(blank=True, default="")
    quantity_on_hand = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    unit_of_measure = models.CharField(max_length=10, choices=UnitOfMeasure.choices)
    reorder_point = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    notes = models.TextField(blank=True, default="")
    earmarked_for: models.ManyToManyField[Recipe, InventoryItem] = (
        models.ManyToManyField(
            "Recipe",
            blank=True,
            related_name="earmarked_items",
        )
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items_updated",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def is_low_stock(self) -> bool:
        """Return True if quantity is at or below the reorder point."""
        return self.quantity_on_hand <= self.reorder_point

    @property
    def subcategory_display(self) -> str:
        """Return human-readable subcategory label."""
        return Subcategory(self.subcategory).label


class RecipeIngredient(models.Model):
    """An ingredient used in a recipe with its quantity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredients",
    )
    ingredient = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="recipe_usages",
        limit_choices_to={"category": Category.INGREDIENT},
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UnitOfMeasure.choices)

    class Meta:
        ordering = ["ingredient__subcategory", "ingredient__name"]
        unique_together = ["recipe", "ingredient"]

    def __str__(self) -> str:
        return f"{self.ingredient.name}: {self.amount} {self.unit}"
