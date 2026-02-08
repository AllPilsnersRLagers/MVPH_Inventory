"""Inventory models for brewery inventory management."""

import uuid
from decimal import Decimal

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
