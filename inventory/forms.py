"""Forms for inventory management."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django import forms

from .models import SUBCATEGORY_MAP, InventoryItem, Recipe


class InventoryItemForm(forms.ModelForm):  # type: ignore[type-arg]
    """Form for creating and updating inventory items."""

    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "subcategory",
            "description",
            "quantity_on_hand",
            "unit_of_measure",
            "reorder_point",
            "notes",
            "earmarked_for",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.category:
            choices = SUBCATEGORY_MAP.get(self.instance.category, [])
            self.fields["subcategory"].choices = [  # type: ignore[attr-defined]
                ("", "---------"),
                *choices,
            ]
        # earmarked_for is only meaningful for ingredients, but we always
        # include it in the form and let the template handle visibility
        self.fields["earmarked_for"].required = False
        self.fields["earmarked_for"].widget = forms.CheckboxSelectMultiple()


class RecipeForm(forms.ModelForm):  # type: ignore[type-arg]
    """Form for creating and updating recipes."""

    class Meta:
        model = Recipe
        fields = ["name"]


class QuickRecipeForm(forms.ModelForm):  # type: ignore[type-arg]
    """Minimal form for quick-adding a recipe from the item form."""

    class Meta:
        model = Recipe
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "New recipe name..."}),
        }


class StockAdjustmentForm(forms.Form):
    """Form for quick stock adjustments."""

    adjustment = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.1", "autofocus": True}),
        help_text="Positive to add, negative to subtract.",
    )

    def apply_to(self, item: InventoryItem) -> InventoryItem:
        """Apply the stock adjustment to the given item."""
        adjustment: Decimal = self.cleaned_data["adjustment"]
        item.quantity_on_hand += adjustment
        if item.quantity_on_hand < Decimal("0.00"):
            item.quantity_on_hand = Decimal("0.00")
        item.save(update_fields=["quantity_on_hand", "updated_at"])
        return item
