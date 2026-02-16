"""Inventory models for brewery inventory management."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

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
    manufacturer = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Manufacturer or supplier name (e.g., Briess, Rahr, Viking)",
    )
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
        ordering = ["name", "manufacturer"]

    def __str__(self) -> str:
        if self.manufacturer:
            return f"{self.name} ({self.manufacturer})"
        return self.name

    @property
    def is_low_stock(self) -> bool:
        """Return True if quantity is at or below the reorder point."""
        return self.quantity_on_hand <= self.reorder_point

    @property
    def stock_status(self) -> str:
        """Return stock status: 'reorder', 'low', or 'ok'."""
        if self.quantity_on_hand <= self.reorder_point:
            return "reorder"
        # Within 10% of reorder point
        threshold = self.reorder_point * Decimal("1.10")
        if self.quantity_on_hand <= threshold:
            return "low"
        return "ok"

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


class ActionType(models.TextChoices):
    """Types of actions that can be logged."""

    CREATED = "created", "Created"
    UPDATED = "updated", "Updated"
    STOCK_ADJUSTED = "stock_adjusted", "Stock Adjusted"


class ItemChangeLog(models.Model):
    """Audit log for changes to inventory items."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="change_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="item_changes",
    )
    action = models.CharField(max_length=20, choices=ActionType.choices)
    field_name = models.CharField(max_length=50, blank=True, default="")
    old_value = models.TextField(blank=True, default="")
    new_value = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["item", "-created_at"]),
        ]

    def __str__(self) -> str:
        if self.field_name:
            return f"{self.action}: {self.field_name} changed"
        return f"{self.action}"


# Fields to track for change logging
TRACKED_FIELDS = [
    "name",
    "manufacturer",
    "category",
    "subcategory",
    "description",
    "quantity_on_hand",
    "unit_of_measure",
    "reorder_point",
    "notes",
]


def capture_item_state(item: InventoryItem) -> dict[str, str]:
    """Capture the current state of tracked fields as strings."""
    state: dict[str, str] = {}
    for field in TRACKED_FIELDS:
        value = getattr(item, field)
        state[field] = str(value) if value is not None else ""
    # Handle M2M separately - must be saved first
    if item.pk:
        recipes = list(item.earmarked_for.values_list("name", flat=True))
        state["earmarked_for"] = ", ".join(sorted(recipes)) if recipes else ""
    else:
        state["earmarked_for"] = ""
    return state


def log_item_changes(
    item: InventoryItem,
    user: Any,
    action: str,
    old_state: dict[str, str] | None = None,
    new_state: dict[str, str] | None = None,
) -> list[ItemChangeLog]:
    """Create change log entries for an item.

    For 'created' action: Creates a single log entry with no field details.
    For 'updated'/'stock_adjusted': Creates one entry per changed field.
    """
    logs: list[ItemChangeLog] = []

    if action == ActionType.CREATED:
        logs.append(
            ItemChangeLog.objects.create(
                item=item,
                user=user,
                action=action,
            )
        )
    elif old_state and new_state:
        for field in [*TRACKED_FIELDS, "earmarked_for"]:
            old_val = old_state.get(field, "")
            new_val = new_state.get(field, "")
            if old_val != new_val:
                logs.append(
                    ItemChangeLog.objects.create(
                        item=item,
                        user=user,
                        action=action,
                        field_name=field,
                        old_value=old_val,
                        new_value=new_val,
                    )
                )

    return logs
